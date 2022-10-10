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
import logging
import os

from django.conf import settings
from django.core.management import call_command

from celery import shared_task
from celery.utils.log import get_task_logger

from geonode.celery_app import app
from geonode.tasks.tasks import (
    AcquireLock,
    FaultTolerantTask)
from geonode.base.models import Link
from geonode.base import enumerations
from geonode.layers.models import Dataset
from geonode.base.models import ResourceBase

from .security import sync_resources_with_guardian
from .helpers import (
    gs_slurp,
    gs_catalog,
    set_styles,
    get_sld_for,
    set_dataset_style,
    cascading_delete,
    create_gs_thumbnail,
    sync_instance_with_geoserver)

logger = get_task_logger(__name__)

log_lock = logging.getLogger("geonode_lock_handler")


@app.task(
    bind=True,
    base=FaultTolerantTask,
    name='geonode.geoserver.tasks.geoserver_update_datasets',
    queue='geoserver.catalog',
    expires=600,
    time_limit=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 5},
    retry_backoff=3,
    retry_backoff_max=30,
    retry_jitter=False)
def geoserver_update_datasets(self, *args, **kwargs):
    """
    Runs update layers.
    """
    lock_id = f'{self.request.id}'
    log_lock.debug(f"geoserver_update_datasets: Creating lock {lock_id}")
    with AcquireLock(lock_id) as lock:
        log_lock.debug(f"geoserver_update_datasets: Acquiring lock {lock_id}")
        if lock.acquire() is True:
            log_lock.debug(f"geoserver_update_datasets: Acquired lock {lock_id}")
            try:
                return gs_slurp(*args, **kwargs)
            finally:
                lock.release()
                log_lock.debug(f"geoserver_update_datasets: Released lock {lock_id}")


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
        instance = Dataset.objects.get(id=instance_id)
    except Dataset.DoesNotExist:
        logger.debug(f"Dataset id {instance_id} does not exist yet!")
        raise

    lock_id = f'{self.request.id}' if self.request.id else instance.name
    log_lock.debug(f"geoserver_set_style: Creating lock {lock_id} for {instance.name}")
    with AcquireLock(lock_id) as lock:
        log_lock.debug(f"geoserver_set_style: Acquiring lock {lock_id} for {instance.name}")
        if lock.acquire() is True:
            log_lock.debug(f"geoserver_set_style: Acquired lock {lock_id} for {instance.name}")
            try:
                sld = None
                if os.path.exists(base_file):
                    sld = open(base_file, "rb").read()
                else:
                    sld = base_file
                    base_file = None

                set_dataset_style(
                    instance,
                    instance.alternate,
                    sld,
                    base_file=base_file)

            except Exception as e:
                logger.exception(e)
            finally:
                lock.release()
                log_lock.debug(f"geoserver_set_style: Released lock {lock_id} for {instance.name}")


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
    from geonode.geoserver.signals import geoserver_automatic_default_style_set
    instance = None
    try:
        instance = Dataset.objects.get(id=instance_id)
    except Dataset.DoesNotExist:
        logger.debug(f"Dataset id {instance_id} does not exist yet!")
        raise

    lock_id = f'{self.request.id}' if self.request.id else instance.name
    log_lock.debug(f"geoserver_create_style: Creating lock {lock_id} for {instance.name}")
    with AcquireLock(lock_id) as lock:
        log_lock.debug(f"geoserver_create_style: Acquiring lock {lock_id} for {instance.name}")
        if lock.acquire() is True:
            log_lock.debug(f"geoserver_create_style: Acquired lock {lock_id} for {instance.name}")
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
                            gs_dataset = gs_catalog.get_layer(name)
                            _default_style = gs_dataset.default_style
                            gs_dataset.default_style = style
                            gs_catalog.save(gs_dataset)
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
                if not f:
                    # this signal is used by the mapstore client to set the style in visual mode
                    geoserver_automatic_default_style_set.send_robust(sender=instance, instance=instance)
            finally:
                lock.release()
                log_lock.debug(f"geoserver_create_style: Released lock {lock_id} for {instance.name}")


@app.task(
    bind=True,
    base=FaultTolerantTask,
    name='geonode.geoserver.tasks.geoserver_post_save_datasets',
    queue='geoserver.catalog',
    expires=600,
    time_limit=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 5},
    retry_backoff=3,
    retry_backoff_max=30,
    retry_jitter=False)
def geoserver_post_save_datasets(
        self,
        instance_id,
        *args, **kwargs):
    """
    Runs update layers.
    """
    instance = None
    try:
        instance = Dataset.objects.get(id=instance_id)
    except Dataset.DoesNotExist:
        logger.debug(f"Dataset id {instance_id} does not exist yet!")
        raise

    lock_id = f'{self.request.id}' if self.request.id else instance.name
    log_lock.debug(f"geoserver_post_save_datasets: Creating lock {lock_id} for {instance_id}")
    with AcquireLock(lock_id) as lock:
        log_lock.debug(f"geoserver_post_save_datasets: Acquiring lock {lock_id} for {instance_id}")
        if lock.acquire() is True:
            log_lock.debug(f"geoserver_post_save_datasets: Acquired lock {lock_id} for {instance_id}")
            try:
                sync_instance_with_geoserver(instance_id, *args, **kwargs)

                # Updating HAYSTACK Indexes if needed
                if settings.HAYSTACK_SEARCH:
                    call_command('update_index')
            finally:
                lock.release()
                log_lock.debug(f"geoserver_post_save_datasets: Releasing lock {lock_id} for {instance_id}")


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

    lock_id = f'{self.request.id}' if self.request.id else instance.name
    log_lock.debug(f"geoserver_create_thumbnail: Creating lock {lock_id} for {instance.name}")
    with AcquireLock(lock_id) as lock:
        log_lock.debug(f"geoserver_create_thumbnail: Acquiring lock {lock_id} for {instance.name}")
        if lock.acquire() is True:
            log_lock.debug(f"geoserver_create_thumbnail: Acquired lock {lock_id} for {instance.name}")
            try:
                instance.set_processing_state(enumerations.STATE_RUNNING)
                try:
                    instance.set_dirty_state()
                    create_gs_thumbnail(instance, overwrite=overwrite, check_bbox=check_bbox)
                    logger.debug(f"... Created Thumbnail for Dataset {instance.title}")
                except Exception as e:
                    geoserver_create_thumbnail.retry(exc=e)
                finally:
                    instance.set_processing_state(enumerations.STATE_PROCESSED)
            finally:
                lock.release()
                log_lock.debug(f"geoserver_create_thumbnail: Released lock {lock_id} for {instance.name}")


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


@app.task(
    bind=True,
    name='geonode.geoserver.tasks.geoserver_delete_map',
    queue='cleanup',
    expires=600,
    time_limit=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 5},
    retry_backoff=3,
    retry_backoff_max=30,
    retry_jitter=False)
def geoserver_delete_map(self, object_id):
    """
    Deletes a map and the associated map layers.
    """
    from geonode.maps.models import Map
    lock_id = f'{self.request.id}'
    with AcquireLock(lock_id) as lock:
        if lock.acquire() is True:
            try:
                try:
                    map_obj = Map.objects.get(id=object_id)
                except Map.DoesNotExist:
                    return

                map_obj.maplayers.all().delete()
                map_obj.delete()
            finally:
                lock.release()


@shared_task(
    bind=True,
    name='geonode.security.tasks.synch_guardian',
    queue='security',
    expires=600,
    time_limit=600,
    acks_late=False,
    autoretry_for=(Exception, ),
    retry_kwargs={'max_retries': 5},
    retry_backoff=3,
    retry_backoff_max=30,
    retry_jitter=False)
def synch_guardian():
    """
    Sync resources with Guardian and clear their dirty state
    """
    if getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
        sync_resources_with_guardian()
