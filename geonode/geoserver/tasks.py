#########################################################################
#
# Copyright (C) 2017 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
import os
import shutil

from django.conf import settings
from django.core.management import call_command

from celery.utils.log import get_task_logger

from geonode.celery_app import app
from geonode.tasks.tasks import (
    AcquireLock,
    FaultTolerantTask)
from geonode.upload import signals
from geonode.layers.models import (
    Layer, UploadSession)
from geonode.base.models import (
    Link,
    ResourceBase)

from .helpers import (
    gs_catalog,
    gs_slurp,
    set_styles,
    get_sld_for,
    set_layer_style,
    cascading_delete,
    create_gs_thumbnail,
    sync_instance_with_geoserver)

logger = get_task_logger(__name__)


@app.task(
    bind=True,
    base=FaultTolerantTask,
    name='geonode.geoserver.tasks.geoserver_update_layers',
    queue='geoserver.catalog',
    expires=600,
    time_limit=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 5},
    retry_backoff=3,
    retry_backoff_max=30,
    retry_jitter=False)
def geoserver_update_layers(self, *args, **kwargs):
    """
    Runs update layers.
    """
    lock_id = f'{self.request.id}'
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True:
            try:
                return gs_slurp(*args, **kwargs)
            finally:
                lock.release()


@app.task(
    bind=True,
    base=FaultTolerantTask,
    name='geonode.geoserver.tasks.geoserver_set_style',
    queue='geoserver.catalog',
    expires=600,
    time_limit=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 5},
    retry_backoff=3,
    retry_backoff_max=30,
    retry_jitter=False)
def geoserver_set_style(
        self,
        instance_id,
        base_file):
    """
    Sets styles from SLD file.
    """
    instance = None
    try:
        instance = Layer.objects.get(id=instance_id)
    except Layer.DoesNotExist:
        logger.debug(f"Layer id {instance_id} does not exist yet!")
        raise

    lock_id = f'{self.request.id}'
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True:
            try:
                sld = open(base_file, "rb").read()
                set_layer_style(
                    instance,
                    instance.alternate,
                    sld,
                    base_file=base_file)
            except Exception as e:
                logger.exception(e)
            finally:
                lock.release()


@app.task(
    bind=True,
    base=FaultTolerantTask,
    name='geonode.geoserver.tasks.geoserver_create_style',
    queue='geoserver.catalog',
    expires=600,
    time_limit=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 5},
    retry_backoff=3,
    retry_backoff_max=30,
    retry_jitter=False)
def geoserver_create_style(
        self,
        instance_id,
        name,
        sld_file,
        tempdir):
    """
    Sets or create styles from Upload Session.
    """
    instance = None
    try:
        instance = Layer.objects.get(id=instance_id)
    except Layer.DoesNotExist:
        logger.debug(f"Layer id {instance_id} does not exist yet!")
        raise

    lock_id = f'{self.request.id}'
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True and instance:
            try:
                f = None
                if sld_file and os.path.exists(sld_file) and os.access(sld_file, os.R_OK):
                    if os.path.isfile(sld_file):
                        try:
                            f = open(sld_file)
                        except Exception:
                            pass
                    elif tempdir and os.path.exists(tempdir):
                        if os.path.isfile(os.path.join(tempdir, sld_file)):
                            try:
                                f = open(os.path.join(tempdir, sld_file))
                            except Exception:
                                pass
                    if f:
                        sld = f.read()
                        f.close()
                        if not gs_catalog.get_style(name=name, workspace=settings.DEFAULT_WORKSPACE):
                            style = gs_catalog.create_style(
                                name,
                                sld,
                                raw=True,
                                workspace=settings.DEFAULT_WORKSPACE)
                            gs_layer = gs_catalog.get_layer(name)
                            _default_style = gs_layer.default_style
                            gs_layer.default_style = style
                            gs_catalog.save(gs_layer)
                            set_styles(instance, gs_catalog)
                            try:
                                gs_catalog.delete(_default_style)
                                Link.objects.filter(
                                    resource=instance.resourcebase_ptr,
                                    name='Legend',
                                    url__contains=f'STYLE={_default_style.name}').delete()
                            except Exception as e:
                                logger.exception(e)
                    else:
                        get_sld_for(gs_catalog, instance)
                else:
                    get_sld_for(gs_catalog, instance)
            finally:
                lock.release()


@app.task(
    bind=True,
    base=FaultTolerantTask,
    name='geonode.geoserver.tasks.geoserver_finalize_upload',
    queue='geoserver.events',
    expires=600,
    time_limit=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 5},
    retry_backoff=3,
    retry_backoff_max=30,
    retry_jitter=False)
def geoserver_finalize_upload(
        self,
        import_id,
        instance_id,
        permissions,
        created,
        xml_file,
        sld_file,
        sld_uploaded,
        tempdir):
    """
    Finalize Layer and GeoServer configuration:
     - Sets Layer Metadata from XML and updates GeoServer Layer accordingly.
     - Sets Default Permissions
    """
    instance = None
    try:
        instance = Layer.objects.get(id=instance_id)
    except Layer.DoesNotExist as e:
        logger.debug(f"Layer id {instance_id} does not exist yet!")
        geoserver_finalize_upload.retry(exc=e)

    lock_id = f'{self.request.id}'
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True:
            try:
                # Hide the resource until finished
                instance.set_processing_state("RUNNING")

                from geonode.upload.models import Upload
                upload = Upload.objects.get(import_id=import_id)
                upload.layer = instance
                upload.save()
                upload.set_processing_state(Upload.STATE_RUNNING)

                try:
                    # Update the upload sessions
                    geonode_upload_sessions = UploadSession.objects.filter(resource=instance)
                    geonode_upload_sessions.update(processed=False)
                    instance.upload_session = geonode_upload_sessions.first()
                except Exception as e:
                    logger.exception(e)
                    geoserver_finalize_upload.retry(exc=e)

                # Sanity checks
                if isinstance(xml_file, list):
                    if len(xml_file) > 0:
                        xml_file = xml_file[0]
                    else:
                        xml_file = None
                elif not isinstance(xml_file, str):
                    xml_file = None

                if xml_file and os.path.exists(xml_file) and os.access(xml_file, os.R_OK):
                    instance.metadata_uploaded = True

                try:
                    gs_resource = gs_catalog.get_resource(
                        name=instance.name,
                        store=instance.store,
                        workspace=instance.workspace)
                except Exception:
                    try:
                        gs_resource = gs_catalog.get_resource(
                            name=instance.alternate,
                            store=instance.store,
                            workspace=instance.workspace)
                    except Exception:
                        try:
                            gs_resource = gs_catalog.get_resource(
                                name=instance.alternate or instance.typename)
                        except Exception:
                            gs_resource = None

                if gs_resource:
                    # Updating GeoServer resource
                    gs_resource.title = instance.title
                    gs_resource.abstract = instance.abstract
                    gs_catalog.save(gs_resource)
                    if gs_resource.store:
                        instance.storeType = gs_resource.store.resource_type
                        if not instance.alternate:
                            instance.alternate = f"{gs_resource.store.workspace.name}:{gs_resource.name}"

                if sld_uploaded:
                    geoserver_set_style(instance.id, sld_file)
                else:
                    geoserver_create_style(instance.id, instance.name, sld_file, tempdir)

                logger.debug(f'Finalizing (permissions and notifications) Layer {instance}')
                instance.handle_moderated_uploads()

                if permissions is not None:
                    logger.debug(f'Setting permissions {permissions} for {instance.name}')
                    instance.set_permissions(permissions)

                instance.save(notify=not created)

                try:
                    logger.debug(f"... Cleaning up the temporary folders {tempdir}")
                    if tempdir and os.path.exists(tempdir):
                        shutil.rmtree(tempdir)
                except Exception as e:
                    logger.warning(e)

                try:
                    # Update the upload sessions
                    geonode_upload_sessions = UploadSession.objects.filter(resource=instance)
                    geonode_upload_sessions.update(processed=True)
                    instance.upload_session = geonode_upload_sessions.first()
                    upload.complete = True
                    upload.save()
                    upload.set_processing_state(Upload.STATE_PROCESSED)
                except Exception as e:
                    logger.exception(e)
                    upload.complete = False
                    upload.save()
                    upload.set_processing_state(Upload.STATE_INVALID)
                    geoserver_finalize_upload.retry(exc=e)

                signals.upload_complete.send(sender=geoserver_finalize_upload, layer=instance)
            finally:
                lock.release()


@app.task(
    bind=True,
    base=FaultTolerantTask,
    name='geonode.geoserver.tasks.geoserver_post_save_layers',
    queue='geoserver.catalog',
    expires=600,
    time_limit=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 5},
    retry_backoff=3,
    retry_backoff_max=30,
    retry_jitter=False)
def geoserver_post_save_layers(
        self,
        instance_id,
        *args, **kwargs):
    """
    Runs update layers.
    """
    lock_id = f'{self.request.id}'
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True:
            try:
                sync_instance_with_geoserver(instance_id, *args, **kwargs)

                # Updating HAYSTACK Indexes if needed
                if settings.HAYSTACK_SEARCH:
                    call_command('update_index')
            finally:
                lock.release()


@app.task(
    bind=True,
    base=FaultTolerantTask,
    name='geonode.geoserver.tasks.geoserver_create_thumbnail',
    queue='geoserver.events',
    expires=600,
    time_limit=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 5},
    retry_backoff=3,
    retry_backoff_max=30,
    retry_jitter=False)
def geoserver_create_thumbnail(self, instance_id, overwrite=True, check_bbox=True):
    """
    Runs create_gs_thumbnail.
    """
    instance = None
    try:
        instance = ResourceBase.objects.get(id=instance_id).get_real_instance()
    except Exception:
        logger.error(f"Resource id {instance_id} does not exist yet!")
        raise

    lock_id = f'{self.request.id}'
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True:
            try:
                create_gs_thumbnail(instance, overwrite=overwrite, check_bbox=check_bbox)
                logger.debug(f"... Created Thumbnail for Layer {instance.title}")
            except Exception as e:
                geoserver_create_thumbnail.retry(exc=e)
            finally:
                lock.release()


@app.task(
    bind=True,
    base=FaultTolerantTask,
    name='geonode.geoserver.tasks.geoserver_cascading_delete',
    queue='cleanup',
    expires=600,
    time_limit=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 5},
    retry_backoff=3,
    retry_backoff_max=30,
    retry_jitter=False)
def geoserver_cascading_delete(self, *args, **kwargs):
    """
    Runs cascading_delete.
    """
    lock_id = f'{self.request.id}'
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True:
            try:
                return cascading_delete(*args, **kwargs)
            finally:
                lock.release()
