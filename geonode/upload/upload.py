#########################################################################
#
# Copyright (C) 2016 OSGeo
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

"""
Provide views and business logic of doing an upload.

The upload process may be multi step so views are all handled internally here
by the view function.

The pattern to support separation of view/logic is each step in the upload
process is suffixed with "_step". The view for that step is suffixed with
"_step_view". The goal of separation of view/logic is to support various
programmatic uses of this API. The logic steps should not accept request objects
or return response objects.

State is stored in a UploaderSession object stored in the user's session.
This needs to be made more stateful by adding a model.
"""
import pytz
import uuid
import shutil
import logging
import os.path
import zipfile
import datetime

from django.conf import settings
from django.db.models import Max
from django.core.files import File
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils.translation import ugettext_lazy as _

import geoserver
import gsimporter

from geonode import GeoNodeException
from geoserver.resource import Coverage
from geoserver.resource import FeatureType
from geonode.tasks.tasks import AcquireLock
from geonode.layers.models import TIME_REGEX_FORMAT
from geonode.upload import UploadException, LayerNotReady
from geonode.base.models import ResourceBase, SpatialRepresentationType, TopicCategory

from ..people.utils import get_default_user
from ..layers.metadata import convert_keyword, parse_metadata
from ..layers.utils import get_valid_layer_name, is_vector, resolve_regions
from ..layers.models import Layer, UploadSession
from ..geoserver.tasks import geoserver_finalize_upload
from ..geoserver.helpers import (
    create_geoserver_db_featurestore,
    set_time_info,
    gs_catalog,
    gs_uploader,
    import_imagemosaic_granules,
    ogc_server_settings
)
from . import utils
from .models import Upload
from .upload_preprocessing import preprocess_files

logger = logging.getLogger(__name__)


def _log(msg, *args, level='error'):
    # this logger is used also for debug purpose with error level
    getattr(logger, level)(msg, *args)


class UploaderSession:

    """All objects held must be able to survive a good pickling"""

    # the gsimporter session object
    import_session = None

    # if provided, this file will be uploaded to geoserver and set as
    # the default
    import_sld_file = None

    # location of any temporary uploaded files
    tempdir = None

    # the main uploaded file, zip, shp, tif, etc.
    base_file = None

    # the name to try to give the layer
    name = None

    # the input file charset
    charset = 'UTF-8'

    # blob of permissions JSON
    permissions = None

    # store most recently configured time transforms to support deleting
    time_transforms = None

    # defaults to REPLACE if not provided. Accepts APPEND, too
    update_mode = None

    # Configure Time for this Layer
    time = None

    # the title given to the layer
    layer_title = None

    # the abstract
    layer_abstract = None

    # track the most recently completed upload step
    completed_step = None

    # track the most recently completed upload step
    error_msg = None

    # the upload type - see the _pages dict in views
    upload_type = None

    # whether the files have been uploaded or provided locally
    spatial_files_uploaded = True

    # time related info - need to store here until geoserver layer exists
    time_info = None

    # whether the user has selected a time dimension for ImageMosaic granules
    # or not
    mosaic = None
    append_to_mosaic_opts = None
    append_to_mosaic_name = None
    mosaic_time_regex = None
    mosaic_time_value = None

    # the user who started this upload session
    user = None

    def __init__(self, **kw):
        for k, v in kw.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise Exception(f'not handled : {k}')

    def cleanup(self):
        """do what we should at the given state of the upload"""
        pass


def upload(
        name,
        base_file,
        charset,
        user=None,
        time_attribute=None,
        time_transform_type=None,
        end_time_attribute=None,
        end_time_transform_type=None,
        presentation_strategy=None,
        precision_value=None,
        precision_step=None,
        use_big_date=False,
        overwrite=False,
        mosaic=False,
        append_to_mosaic_opts=None,
        append_to_mosaic_name=None,
        mosaic_time_regex=None,
        mosaic_time_value=None,
        time_presentation=None,
        time_presentation_res=None,
        time_presentation_default_value=None,
        time_presentation_reference_value=None):

    if user is None:
        user = get_default_user()
    if isinstance(user, str):
        user = get_user_model().objects.get(username=user)
    import_session, upload = save_step(
        user,
        name,
        base_file,
        overwrite,
        mosaic=mosaic,
        append_to_mosaic_opts=append_to_mosaic_opts,
        append_to_mosaic_name=append_to_mosaic_name,
        mosaic_time_regex=mosaic_time_regex,
        mosaic_time_value=mosaic_time_value,
        time_presentation=time_presentation,
        time_presentation_res=time_presentation_res,
        time_presentation_default_value=time_presentation_default_value,
        time_presentation_reference_value=time_presentation_reference_value)
    upload_session = UploaderSession(
        base_file=base_file,
        name=name,
        charset=charset,
        import_session=import_session,
        layer_abstract="",
        layer_title=name,
        permissions=None,
        mosaic=mosaic,
        append_to_mosaic_opts=append_to_mosaic_opts,
        append_to_mosaic_name=append_to_mosaic_name,
        mosaic_time_regex=mosaic_time_regex,
        mosaic_time_value=mosaic_time_value
    )
    time_step(
        upload_session,
        time_attribute, time_transform_type,
        presentation_strategy, precision_value, precision_step,
        end_time_attribute=end_time_attribute,
        end_time_transform_type=end_time_transform_type,
        time_format=None)
    utils.run_import(upload_session, async_upload=False)
    final_step(upload_session, user, charset=charset)


def _get_next_id():
    # importer tracks ids by autoincrement but is prone to corruption
    # which potentially may reset the id - hopefully prevent this...
    upload_next_id = list(Upload.objects.all().aggregate(
        Max('import_id')).values())[0]
    upload_next_id = upload_next_id if upload_next_id else 0
    # next_id = next_id + 1 if next_id else 1
    importer_sessions = gs_uploader.get_sessions()
    last_importer_session = importer_sessions[len(
        importer_sessions) - 1].id if importer_sessions else 0
    next_id = max(int(last_importer_session), int(upload_next_id)) + 1
    return next_id


def _check_geoserver_store(store_name, layer_type, overwrite):
    """Check if the store exists in geoserver"""
    try:
        store = gs_catalog.get_store(store_name)
    except geoserver.catalog.FailedRequestError:
        pass  # There is no store, ergo the road is clear
    else:
        if store:
            resources = store.get_resources()
            if len(resources) == 0:
                if overwrite:
                    logger.debug("Deleting previously existing store")
                    store.delete()
                else:
                    raise GeoNodeException(_("Layer already exists"))
            else:
                for resource in resources:
                    if resource.name == store_name:
                        if not overwrite:
                            raise GeoNodeException(
                                _("Name already in use and overwrite is False"))
                        existing_type = resource.resource_type
                        if existing_type != layer_type:
                            msg = (f"Type of uploaded file {store_name} ({layer_type}) does not "
                                   "match type of existing resource type "
                                   f"{existing_type}")
                            logger.error(msg)
                            raise GeoNodeException(msg)


def _get_layer_type(spatial_files):
    if spatial_files.archive is not None:
        the_layer_type = FeatureType.resource_type
    else:
        the_layer_type = spatial_files[0].file_type.layer_type
    return the_layer_type


def save_step(user, layer, spatial_files, overwrite=True, store_spatial_files=True,
              mosaic=False, append_to_mosaic_opts=None, append_to_mosaic_name=None,
              mosaic_time_regex=None, mosaic_time_value=None,
              time_presentation=None, time_presentation_res=None,
              time_presentation_default_value=None,
              time_presentation_reference_value=None,
              charset_encoding="UTF-8", target_store=None):
    lock_id = 'upload_workflow_save_step'
    with AcquireLock(lock_id, blocking=True) as lock:
        if lock.acquire() is True:
            _log(f'Uploading layer: {layer}, files {spatial_files}')
            if len(spatial_files) > 1:
                # we only support more than one file if they're rasters for mosaicing
                if not all(
                        [f.file_type.layer_type == 'coverage' for f in spatial_files]):
                    msg = "Please upload only one type of file at a time"
                    logger.exception(Exception(msg))
                    raise UploadException(msg)
            name = get_valid_layer_name(layer, overwrite)
            _log(f'Name for layer: {name}')
            if not any(spatial_files.all_files()):
                msg = "Unable to recognize the uploaded file(s)"
                logger.exception(Exception(msg))
                raise UploadException(msg)
            the_layer_type = _get_layer_type(spatial_files)
            _check_geoserver_store(name, the_layer_type, overwrite)
            if the_layer_type not in (
                    FeatureType.resource_type,
                    Coverage.resource_type):
                msg = f"Expected layer type to FeatureType or Coverage, not {the_layer_type}"
                logger.exception(Exception(msg))
                raise RuntimeError(msg)
            files_to_upload = preprocess_files(spatial_files)
            _log(f"files_to_upload: {files_to_upload}")
            _log(f'Uploading {the_layer_type}')
            error_msg = None
            try:
                upload = None
                if Upload.objects.filter(user=user, name=name).exists():
                    upload = Upload.objects.filter(user=user, name=name).order_by('-date').first()
                if upload:
                    if upload.state == Upload.STATE_READY:
                        import_session = upload.get_session.import_session
                    else:
                        upload = None
                if not upload:
                    next_id = _get_next_id()
                    # Truncate name to maximum length defined by the field.
                    max_length = Upload._meta.get_field('name').max_length
                    name = name[:max_length]
                    # save record of this whether valid or not - will help w/ debugging
                    upload = Upload.objects.create(
                        user=user,
                        name=name,
                        state=Upload.STATE_READY,
                        upload_dir=spatial_files.dirname
                    )
                    upload.store_spatial_files = store_spatial_files

                    # @todo settings for use_url or auto detection if geoserver is
                    # on same host

                    # Is it a regular file or an ImageMosaic?
                    # if mosaic_time_regex and mosaic_time_value:
                    if mosaic:  # we want to ingest as ImageMosaic
                        target_store, files_to_upload = import_imagemosaic_granules(
                            spatial_files,
                            append_to_mosaic_opts,
                            append_to_mosaic_name,
                            mosaic_time_regex,
                            mosaic_time_value,
                            time_presentation,
                            time_presentation_res,
                            time_presentation_default_value,
                            time_presentation_reference_value)
                        upload.mosaic = mosaic
                        upload.append_to_mosaic_opts = append_to_mosaic_opts
                        upload.append_to_mosaic_name = append_to_mosaic_name
                        upload.mosaic_time_regex = mosaic_time_regex
                        upload.mosaic_time_value = mosaic_time_value
                        # moving forward with a regular Importer session
                        if len(files_to_upload) > 1:
                            import_session = gs_uploader.upload_files(
                                files_to_upload[1:],
                                use_url=False,
                                # import_id=next_id,
                                target_store=target_store,
                                charset_encoding=charset_encoding
                            )
                        else:
                            import_session = gs_uploader.upload_files(
                                files_to_upload,
                                use_url=False,
                                # import_id=next_id,
                                target_store=target_store,
                                charset_encoding=charset_encoding
                            )
                        next_id = import_session.id if import_session else None
                        if not next_id:
                            error_msg = 'No valid Importer Session could be found'
                    else:
                        if overwrite:
                            gs_layer = gs_catalog.get_layer(name)
                            _target_store = (
                                gs_layer.resource.store.name
                                if not isinstance(gs_layer.resource, list)
                                else gs_layer.resource[0].store.name
                            )
                            #  opening Import session for the selected layer
                            # Let's reset the connections first
                            gs_catalog._cache.clear()
                            gs_catalog.reset()

                            import_session = gs_uploader.start_import(
                                import_id=next_id, name=name, target_store=_target_store
                            )
                            import_session.upload_task(files_to_upload)
                            task = import_session.tasks[0]
                            #  Changing layer name, mode and target
                            task.set_update_mode("REPLACE")
                            task.layer.set_target_layer_name(name)
                            task.set_target(store_name=_target_store, workspace=gs_layer.resource.workspace.name)
                            #  Starting import process

                            import_session = import_session.reload()
                        else:
                            # moving forward with a regular Importer session
                            import_session = gs_uploader.upload_files(
                                files_to_upload,
                                use_url=False,
                                import_id=next_id,
                                mosaic=False,
                                target_store=target_store,
                                name=name,
                                charset_encoding=charset_encoding
                            )
                            if ogc_server_settings.datastore_db and any(map(is_vector, files_to_upload)):
                                target = create_geoserver_db_featurestore(
                                    # store_name=ogc_server_settings.DATASTORE,
                                    store_name=ogc_server_settings.datastore_db['NAME'],
                                    workspace=settings.DEFAULT_WORKSPACE
                                )
                                task = import_session.tasks[0]
                                task.set_target(store_name=target_store or target.name, workspace=settings.DEFAULT_WORKSPACE)

                    upload.import_id = import_session.id
                    upload.save()

                # any unrecognized tasks/files must be deleted or we can't proceed
                import_session.delete_unrecognized_tasks()

                if not mosaic:
                    if not import_session.tasks:
                        error_msg = 'No valid upload files could be found'
                if import_session.tasks:
                    if import_session.tasks[0].state == 'NO_FORMAT' \
                            or import_session.tasks[0].state == 'BAD_FORMAT':
                        error_msg = 'There may be a problem with the data provided - ' \
                                    'we could not identify its format'
                    elif import_session.tasks[0].state == 'ERROR':
                        task = import_session.tasks[0]
                        error_msg = "Unexpected error durng the GeoServer upload" \
                            "please check GeoServer logs for more information"

                if not mosaic and len(import_session.tasks) > 1:
                    error_msg = "Only a single upload is supported at the moment"

                if not error_msg and import_session.tasks:
                    task = import_session.tasks[0]
                    # single file tasks will have just a file entry
                    if hasattr(task, 'files'):
                        # @todo gsimporter - test this
                        if not all([hasattr(f, 'timestamp')
                                    for f in task.source.files]):
                            error_msg = (
                                "Not all timestamps could be recognized."
                                "Please ensure your files contain the correct formats.")

                if error_msg:
                    upload.set_processing_state(Upload.STATE_INVALID)

                # @todo once the random tmp9723481758915 type of name is not
                # around, need to track the name computed above, for now, the
                # target store name can be used
            except Exception as e:
                logger.exception(e)
                raise e

            if error_msg:
                logger.exception(Exception(error_msg))
                raise UploadException(error_msg)
            else:
                _log("The File [%s] has been sent to GeoServer without errors.", name, level="debug")
            return import_session, upload


def time_step(upload_session, time_attribute, time_transform_type,
              presentation_strategy, precision_value, precision_step,
              end_time_attribute=None,
              end_time_transform_type=None,
              end_time_format=None,
              time_format=None):
    '''
    time_attribute - name of attribute to use as time

    time_transform_type - name of transform. either
    DateFormatTransform or IntegerFieldToDateTransform

    time_format - optional string format
    end_time_attribute - optional name of attribute to use as end time

    end_time_transform_type - optional name of transform. either
    DateFormatTransform or IntegerFieldToDateTransform

    end_time_format - optional string format
    presentation_strategy - LIST, DISCRETE_INTERVAL, CONTINUOUS_INTERVAL
    precision_value - number
    precision_step - year, month, day, week, etc.
    '''
    import_session = upload_session.import_session
    transforms = []

    def build_time_transform(att, type, format, end_time_attribute, presentation_strategy):
        trans = {'type': type, 'field': att}
        if format:
            trans['format'] = format
        if end_time_attribute:
            trans['enddate'] = end_time_attribute
        if presentation_strategy:
            trans['presentation'] = presentation_strategy
        return trans

    def build_att_remap_transform(att):
        # @todo the target is so ugly it should be obvious
        return {'type': 'AttributeRemapTransform',
                'field': att,
                'target': 'org.geotools.data.postgis.PostGISDialect$XDate'}

    use_big_date = getattr(
        settings,
        'USE_BIG_DATE',
        False)

    if time_attribute:
        if time_transform_type:
            transforms.append(
                build_time_transform(
                    time_attribute,
                    time_transform_type,
                    time_format,
                    end_time_attribute,
                    presentation_strategy
                )
            )

        # this must go after the remapping transform to ensure the
        # type change is applied
        if use_big_date:
            transforms.append(build_att_remap_transform(time_attribute))
            if end_time_attribute:

                transforms.append(
                    build_att_remap_transform(end_time_attribute)
                )

        transforms.append({
            'type': 'CreateIndexTransform',
            'field': time_attribute
        })
        # the time_info will be used in the last step to configure the
        # layer in geoserver - the dict matches the arguments of the
        # set_time_info helper function
        upload_session.time_info = dict(
            attribute=time_attribute,
            end_attribute=end_time_attribute,
            presentation=presentation_strategy,
            precision_value=precision_value,
            precision_step=precision_step
        )

    if upload_session.time_transforms:
        import_session.tasks[0].remove_transforms(
            upload_session.time_transforms
        )

    if transforms:
        logger.debug(f'Setting transforms {transforms}')
        import_session.tasks[0].add_transforms(transforms)
        try:
            upload_session.time_transforms = transforms
            upload_session.time = True
        except gsimporter.BadRequest as br:
            logger.exception(br)
            Upload.objects.invalidate_from_session(upload_session)
            raise UploadException.from_exc(_('Error configuring time:'), br)
        import_session.tasks[0].save_transforms()
    else:
        upload_session.time = False
    try:
        import_session = import_session.reload()
    except gsimporter.api.NotFound as e:
        logger.exception(e)
        Upload.objects.invalidate_from_session(upload_session)
        raise UploadException.from_exc(_("The GeoServer Import Session is no more available ") + str(e))
    upload_session.import_session = import_session
    Upload.objects.update_from_session(upload_session)


def csv_step(upload_session, lat_field, lng_field):
    import_session = upload_session.import_session
    task = import_session.tasks[0]

    transform = {'type': 'AttributesToPointGeometryTransform',
                 'latField': lat_field,
                 'lngField': lng_field,
                 }
    task.remove_transforms([transform], by_field='type', save=False)
    task.add_transforms([transform], save=False)
    task.save_transforms()
    try:
        import_session = import_session.reload()
    except gsimporter.api.NotFound as e:
        logger.exception(e)
        Upload.objects.invalidate_from_session(upload_session)
        raise UploadException.from_exc(
            _("The GeoServer Import Session is no more available"), e)
    upload_session.import_session = import_session
    Upload.objects.update_from_session(upload_session)


def srs_step(upload_session, source, target):
    import_session = upload_session.import_session
    task = import_session.tasks[0]
    if source:
        logger.debug('Setting SRS to %s', source)
        task.set_srs(source)

    transform = {
        'type': 'ReprojectTransform',
        'source': source,
        'target': target,
    }
    task.remove_transforms([transform], by_field='type', save=False)
    task.add_transforms([transform], save=False)
    task.save_transforms()
    try:
        import_session = import_session.reload()
    except gsimporter.api.NotFound as e:
        logger.exception(e)
        Upload.objects.invalidate_from_session(upload_session)
        raise UploadException.from_exc(
            _("The GeoServer Import Session is no more available"), e)
    upload_session.import_session = import_session
    Upload.objects.update_from_session(upload_session)


def final_step(upload_session, user, charset="UTF-8", layer_id=None):
    import_session = upload_session.import_session
    if import_session:
        import_id = import_session.id
        saved_layer = None
        lock_id = f'final_step-{import_id}'
        with AcquireLock(lock_id, blocking=True) as lock:
            if lock.acquire() is True:
                _upload = None
                try:
                    _upload = Upload.objects.get(import_id=import_id)
                    saved_layer = _upload.layer
                except Exception as e:
                    logger.exception(e)
                    Upload.objects.invalidate_from_session(upload_session)
                    raise UploadException.from_exc(
                        _("The Upload Session is no more available"), e)

                _log(f'Reloading session {import_id} to check validity')
                try:
                    import_session = gs_uploader.get_session(import_id)
                except gsimporter.api.NotFound as e:
                    logger.exception(e)
                    Upload.objects.invalidate_from_session(upload_session)
                    raise UploadException.from_exc(
                        _("The GeoServer Import Session is no more available"), e)

                if import_session.tasks is None or len(import_session.tasks) == 0:
                    return saved_layer

                task = import_session.tasks[0]
                try:
                    if charset:
                        task.set_charset(charset)
                except Exception as e:
                    logger.exception(e)

                overwrite = task.updateMode == 'REPLACE'
                # @todo see above in save_step, regarding computed unique name
                name = task.layer.name
                target = task.target

                if saved_layer:
                    name = saved_layer.name

                _vals = dict(
                    title=upload_session.layer_title,
                    abstract=upload_session.layer_abstract,
                    alternate=task.get_target_layer_name(),
                    store=target.name,
                    name=task.layer.name,
                    workspace=target.workspace_name
                )

                _log(f'Getting from catalog [{name}]')
                try:
                    # the importer chooses an available featuretype name late in the game need
                    # to verify the resource.name otherwise things will fail.  This happens
                    # when the same data is uploaded a second time and the default name is
                    # chosen
                    gs_catalog.get_layer(name)
                except Exception:
                    Upload.objects.invalidate_from_session(upload_session)
                    raise LayerNotReady(
                        _(f"Expected to find layer named '{name}' in geoserver"))

                _tasks_ready = any([_task.state in ["READY"] for _task in import_session.tasks])
                _tasks_failed = any([_task.state in ["BAD_FORMAT", "ERROR", "CANCELED"] for _task in import_session.tasks])
                _tasks_waiting = any([_task.state in ["NO_CRS", "NO_BOUNDS", "NO_FORMAT"] for _task in import_session.tasks])

                if not saved_layer and not (_tasks_failed or _tasks_waiting) and (
                        import_session.state == Upload.STATE_READY or (import_session.state == Upload.STATE_PENDING and _tasks_ready)):
                    _log(f"final_step: Running Import Session {import_session.id} - target: {target.name} - alternate: {task.get_target_layer_name()}")
                    _log(f" -- session state: {import_session.state} - task state: {task.state}")

                    utils.run_import(upload_session, async_upload=False)

                    import_session = import_session.reload()
                    task = import_session.tasks[0]
                    name = task.layer.name
                    _vals['name'] = task.layer.name
                    _vals['alternate'] = task.get_target_layer_name()
                    _vals['store'] = task.target.name
                    _vals['workspace'] = task.target.workspace_name

                elif import_session.state == Upload.STATE_INCOMPLETE and _tasks_failed:
                    Upload.objects.invalidate_from_session(upload_session)
                    raise Exception(f'unknown item state: {task.state}')
                try:
                    import_session = gs_uploader.get_session(import_id)
                except gsimporter.api.NotFound as e:
                    logger.exception(e)
                    Upload.objects.invalidate_from_session(upload_session)
                    raise UploadException.from_exc(
                        _("The GeoServer Import Session is no more available"), e)

                upload_session.import_session = import_session.reload()
                upload_session = Upload.objects.update_from_session(upload_session, layer=saved_layer)

                _tasks_failed = any([_task.state in ["BAD_FORMAT", "ERROR", "CANCELED"] for _task in import_session.tasks])
                _tasks_waiting = any([_task.state in ["NO_CRS", "NO_BOUNDS", "NO_FORMAT"] for _task in import_session.tasks])

                if import_session.state != Upload.STATE_COMPLETE or _tasks_waiting:
                    if import_session.state == Upload.STATE_PENDING and _tasks_waiting:
                        if any([_task.state == "NO_CRS" for _task in import_session.tasks]):
                            _redirect_to = f"/upload/srs?id={import_session.id}"
                            _upload.set_resume_url(_redirect_to)
                            _upload.set_processing_state(Upload.STATE_WAITING)
                        elif _tasks_failed:
                            _upload.set_processing_state(Upload.STATE_INVALID)
                    return None

                _log(f'Creating Django record for [{name}]')
                if Upload.objects.filter(import_id=import_id).exists():
                    if Upload.objects.filter(import_id=import_id).count() > 1:
                        Upload.objects.invalidate_from_session(upload_session)
                        raise Exception('Import Session failed. More than Upload Session associated to the Importer ID {import_id}')
                    saved_layer = Upload.objects.filter(import_id=import_id).get().layer

                layer_uuid = None

                if saved_layer:
                    saved_layer.refresh_from_db()
                    return saved_layer
                else:
                    _log(f'Django record for [{name}] does not exist, creating with vals: {_vals}')

                regions = []
                keywords = []
                vals = {}
                custom = {}
                # look for xml and finalize Layer metadata
                metadata_uploaded = False
                xml_file = upload_session.base_file[0].xml_files
                if xml_file and os.path.exists(xml_file[0]):
                    try:
                        # get model properties from XML
                        # If it's contained within a zip, need to extract it
                        if upload_session.base_file.archive:
                            archive = upload_session.base_file.archive
                            zf = zipfile.ZipFile(archive, 'r', allowZip64=True)
                            zf.extract(xml_file[0], os.path.dirname(archive))
                            # Assign the absolute path to this file
                            xml_file = f"{os.path.dirname(archive)}/{xml_file[0]}"

                        # Sanity checks
                        if isinstance(xml_file, list):
                            if len(xml_file) > 0:
                                xml_file = xml_file[0]
                            else:
                                xml_file = None
                        elif not isinstance(xml_file, str):
                            xml_file = None

                        if xml_file and os.path.exists(xml_file[0]) and os.access(xml_file, os.R_OK):
                            layer_uuid, vals, regions, keywords, custom = parse_metadata(
                                open(xml_file).read())
                            metadata_uploaded = True
                    except Exception as e:
                        Upload.objects.invalidate_from_session(upload_session)
                        logger.exception(e)
                        raise GeoNodeException(
                            _("Exception occurred while parsing the provided Metadata file."), e)

                # Make sure the layer does not exists already
                if not overwrite and layer_uuid and Layer.objects.filter(uuid=layer_uuid).count():
                    Upload.objects.invalidate_from_session(upload_session)
                    logger.error("The UUID identifier from the XML Metadata is already in use in this system.")
                    raise GeoNodeException(
                        _("The UUID identifier from the XML Metadata is already in use in this system."))

                # Is it a regular file or an ImageMosaic?
                has_time = has_elevation = False
                start = end = None
                if upload_session.mosaic_time_regex and upload_session.mosaic_time_value:
                    has_time = True
                    start = datetime.datetime.strptime(upload_session.mosaic_time_value,
                                                       TIME_REGEX_FORMAT[upload_session.mosaic_time_regex])
                    start = pytz.utc.localize(start, is_dst=False)
                    end = start
                if upload_session.time and upload_session.time_info and upload_session.time_transforms:
                    has_time = True

                if upload_session.mosaic:
                    if not upload_session.append_to_mosaic_opts:
                        saved_dataset_filter = Layer.objects.filter(
                            store=_vals.get('store'),
                            alternate=_vals.get('alternate'),
                            workspace=_vals.get('workspace'),
                            name=_vals.get('name'))
                        if not saved_dataset_filter.exists():
                            saved_layer = Layer.objects.create(
                                uuid=layer_uuid or str(uuid.uuid4()),
                                store=_vals.get('store'),
                                storeType=target.store_type,
                                alternate=_vals.get('alternate'),
                                workspace=_vals.get('workspace'),
                                title=_vals.get('title'),
                                name=_vals.get('name'),
                                abstract=_vals.get('abstract', _('No abstract provided')),
                                owner=user,
                                temporal_extent_start=start,
                                temporal_extent_end=end,
                                is_mosaic=True,
                                has_time=has_time,
                                has_elevation=has_elevation,
                                time_regex=upload_session.mosaic_time_regex)
                            created = True
                        elif saved_dataset_filter.count() == 1:
                            saved_layer = saved_dataset_filter.get()
                            created = False
                        else:
                            raise GeoNodeException(f"There's an incosistent number of Datasets on the DB for {task.layer.name}")
                    else:
                        saved_layer, created = Layer.objects.get_or_create(
                            name=upload_session.append_to_mosaic_name)
                        try:
                            if saved_layer.temporal_extent_start and end:
                                if pytz.utc.localize(
                                        saved_layer.temporal_extent_start,
                                        is_dst=False) < end:
                                    saved_layer.temporal_extent_end = end
                                    Layer.objects.filter(
                                        name=upload_session.append_to_mosaic_name).update(
                                        temporal_extent_end=end)
                                else:
                                    saved_layer.temporal_extent_start = end
                                    Layer.objects.filter(
                                        name=upload_session.append_to_mosaic_name).update(
                                        temporal_extent_start=end)
                        except Exception as e:
                            _log(
                                f"There was an error updating the mosaic temporal extent: {str(e)}")
                else:
                    # The dataset is a standard one, no mosaic options enabled...
                    saved_dataset_filter = Layer.objects.filter(
                        store=_vals.get('store'),
                        alternate=_vals.get('alternate'),
                        workspace=_vals.get('workspace'),
                        name=_vals.get('name'))
                    if not saved_dataset_filter.exists():
                        saved_layer = Layer.objects.create(
                            uuid=layer_uuid or str(uuid.uuid4()),
                            store=_vals.get('store'),
                            storeType=target.store_type,
                            alternate=_vals.get('alternate'),
                            workspace=_vals.get('workspace'),
                            title=_vals.get('title'),
                            name=_vals.get('name'),
                            abstract=_vals.get('abstract', _('No abstract provided')),
                            owner=user,
                            temporal_extent_start=start,
                            temporal_extent_end=end,
                            is_mosaic=False,
                            has_time=has_time,
                            has_elevation=has_elevation,
                            time_regex=upload_session.mosaic_time_regex)
                        created = True
                    elif saved_dataset_filter.count() == 1:
                        saved_layer = saved_dataset_filter.get()
                        created = False
                    else:
                        raise GeoNodeException(f"There's an incosistent number of Datasets on the DB for {task.layer.name}")

                assert saved_layer

                # Hide the dataset until the upload process finishes...
                saved_layer.set_processing_state(Upload.STATE_RUNNING)
                saved_layer.set_dirty_state()
                _log(f" -- Finalizing Upload for {saved_layer}... {Upload.STATE_RUNNING}")

                # Update the state from session...
                upload_session = Upload.objects.update_from_session(upload_session, layer=saved_layer)

                if not created and not overwrite:
                    return saved_layer

                # Finalize the upload...
                # Set default permissions on the newly created layer and send notifications
                permissions = upload_session.permissions

                # Finalize Upload
                try:
                    with transaction.atomic():
                        # Create a new upload session
                        geonode_upload_session, created = UploadSession.objects.get_or_create(
                            resource=saved_layer, user=user
                        )
                        geonode_upload_session.processed = False
                        geonode_upload_session.save()
                        upload_session = Upload.objects.update_from_session(upload_session, layer=saved_layer)

                        # Add them to the upload session (new file fields are created).
                        assigned_name = None

                        # Update Layer with information coming from XML File if available
                        saved_layer = _update_layer_with_xml_info(saved_layer, xml_file, regions, keywords, vals)

                        def _store_file(saved_layer,
                                        geonode_upload_session,
                                        base_file,
                                        assigned_name,
                                        base=False):
                            if os.path.exists(base_file):
                                with open(base_file, 'rb') as f:
                                    file_name, type_name = os.path.splitext(os.path.basename(base_file))
                                    geonode_upload_session.layerfile_set.create(
                                        name=file_name,
                                        base=base,
                                        file=File(
                                            f, name=f'{assigned_name or saved_layer.name}{type_name}'))
                                    # save the system assigned name for the remaining files
                                    if not assigned_name:
                                        the_file = geonode_upload_session.layerfile_set.first().file.name
                                        assigned_name = os.path.splitext(os.path.basename(the_file))[0]

                                return assigned_name

                        if upload_session.base_file:
                            uploaded_files = upload_session.base_file[0]
                            base_file = uploaded_files.base_file
                            aux_files = uploaded_files.auxillary_files
                            sld_files = uploaded_files.sld_files
                            xml_files = uploaded_files.xml_files

                            assigned_name = _store_file(
                                saved_layer,
                                geonode_upload_session,
                                base_file,
                                assigned_name,
                                base=True)

                            for _f in aux_files:
                                _store_file(saved_layer,
                                            geonode_upload_session,
                                            _f,
                                            assigned_name)

                            for _f in sld_files:
                                _store_file(saved_layer,
                                            geonode_upload_session,
                                            _f,
                                            assigned_name)

                            for _f in xml_files:
                                _store_file(saved_layer,
                                            geonode_upload_session,
                                            _f,
                                            assigned_name)

                        # @todo if layer was not created, need to ensure upload target is
                        # same as existing target
                        # Create the points of contact records for the layer
                        _log(f'Creating points of contact records for {name}')
                        saved_layer.poc = user
                        saved_layer.metadata_author = user
                        saved_layer.metadata_uploaded = metadata_uploaded

                        _log('Creating style for [%s]', name)
                        # look for SLD
                        sld_file = upload_session.base_file[0].sld_files
                        sld_uploaded = False
                        if sld_file and os.path.exists(sld_file[0]):
                            # If it's contained within a zip, need to extract it
                            if upload_session.base_file.archive:
                                archive = upload_session.base_file.archive
                                _log(f'using uploaded sld file from {archive}')
                                zf = zipfile.ZipFile(archive, 'r', allowZip64=True)
                                zf.extract(sld_file[0], os.path.dirname(archive), path=upload_session.tempdir)
                                # Assign the absolute path to this file
                                sld_file[0] = f"{os.path.dirname(archive)}/{sld_file[0]}"
                            else:
                                _sld_file = f"{os.path.dirname(upload_session.tempdir)}/{os.path.basename(sld_file[0])}"
                                _log(f"copying [{sld_file[0]}] to [{_sld_file}]")
                                try:
                                    shutil.copyfile(sld_file[0], _sld_file)
                                    sld_file = _sld_file
                                except (IsADirectoryError, shutil.SameFileError) as e:
                                    logger.exception(e)
                                    sld_file = sld_file[0]
                                except Exception as e:
                                    logger.exception(e)
                                    raise UploadException.from_exc(_('Error uploading Dataset'), e)
                            sld_uploaded = True
                        else:
                            # get_files will not find the sld if it doesn't match the base name
                            # so we've worked around that in the view - if provided, it will be here
                            if upload_session.import_sld_file:
                                _log('using provided sld file')
                                base_file = upload_session.base_file
                                sld_file = base_file[0].sld_files[0]
                            sld_uploaded = False
                        _log(f'[sld_uploaded: {sld_uploaded}] sld_file: {sld_file}')

                        if upload_session.time_info:
                            set_time_info(saved_layer, **upload_session.time_info)

                        # Set default permissions on the newly created layer and send notifications
                        geoserver_finalize_upload.apply(
                            (import_session.id, saved_layer.id, permissions, created,
                             xml_file, sld_file, sld_uploaded, upload_session.tempdir))

                        saved_layer = utils.metadata_storers(saved_layer, custom)

                        Upload.objects.filter(layer=saved_layer).update(complete=True)
                        [u.set_processing_state(Upload.STATE_PROCESSED) for u in Upload.objects.filter(layer=saved_layer)]
                except Exception as e:
                    logger.exception(e)
                    Upload.objects.filter(layer=saved_layer).update(complete=False)
                    [u.set_processing_state(Upload.STATE_INVALID) for u in Upload.objects.filter(layer=saved_layer)]
                finally:
                    _log(f" -- Upload completed for {saved_layer}...")

    return saved_layer


def _update_layer_with_xml_info(saved_layer, xml_file, regions, keywords, vals):
    # Updating layer with information coming from the XML file
    xml_file = xml_file[0] if isinstance(xml_file, list) and xml_file else xml_file
    if xml_file and os.path.exists(xml_file):
        saved_layer.metadata_xml = open(xml_file).read()
        regions_resolved, regions_unresolved = resolve_regions(regions)
        keywords.extend(convert_keyword(regions_unresolved))

        # Assign the regions (needs to be done after saving)
        regions_resolved = list(set(regions_resolved))
        if regions_resolved:
            if len(regions_resolved) > 0:
                if not saved_layer.regions:
                    saved_layer.regions = regions_resolved
                else:
                    saved_layer.regions.clear()
                    saved_layer.regions.add(*regions_resolved)

        # Assign the keywords (needs to be done after saving)
        saved_layer = utils.KeywordHandler(saved_layer, keywords).set_keywords()

        # set model properties
        defaults = {}
        for key, value in vals.items():
            if key == 'spatial_representation_type':
                value = SpatialRepresentationType(identifier=value)
            elif key == 'topic_category':
                value, created = TopicCategory.objects.get_or_create(
                    identifier=value,
                    defaults={'description': '', 'gn_description': value})
                key = 'category'
                defaults[key] = value
            else:
                defaults[key] = value

        # Save all the modified information in the instance without triggering signals.
        try:
            if not defaults.get('title', saved_layer.title):
                defaults['title'] = saved_layer.title or saved_layer.name
            if not defaults.get('abstract', saved_layer.abstract):
                defaults['abstract'] = saved_layer.abstract or ''

            to_update = {}
            to_update['charset'] = defaults.pop('charset', saved_layer.charset)
            to_update['storeType'] = defaults.pop('storeType', saved_layer.storeType)
            for _key in ('name', 'workspace', 'store', 'storeType', 'alternate', 'typename'):
                if _key in defaults:
                    to_update[_key] = defaults.pop(_key)
                else:
                    to_update[_key] = getattr(saved_layer, _key)
            to_update.update(defaults)

            with transaction.atomic():
                ResourceBase.objects.filter(
                    id=saved_layer.resourcebase_ptr.id).update(
                    **defaults)
                Layer.objects.filter(id=saved_layer.id).update(**to_update)

                # Refresh from DB
                saved_layer.refresh_from_db()
        except IntegrityError:
            raise
    return saved_layer
