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
import shutil
import os.path
import logging
import zipfile
import datetime
import geoserver
import gsimporter

from geoserver.resource import (
    Coverage,
    FeatureType)

from django.conf import settings
from django.db.models import Max
from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from geonode import GeoNodeException
from geonode.base import enumerations
from geonode.upload import LayerNotReady
from geonode.tasks.tasks import AcquireLock
from geonode.layers.models import TIME_REGEX_FORMAT
from geonode.resource.manager import resource_manager
from geonode.upload.api.exceptions import GeneralUploadException

from ..layers.models import Dataset
from ..layers.metadata import parse_metadata
from ..people.utils import get_default_user
from ..layers.utils import get_valid_dataset_name, is_vector
from ..geoserver.helpers import (
    gs_catalog,
    gs_uploader
)
from . import utils
from .models import Upload
from .upload_preprocessing import preprocess_files
from geonode.geoserver.helpers import (
    get_dataset_type,
    get_dataset_storetype,
    create_geoserver_db_featurestore,
    ogc_server_settings)

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

    # Configure Time for this Dataset
    time = None

    # the title given to the layer
    dataset_title = None

    # the abstract
    dataset_abstract = None

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
        dataset_abstract="",
        dataset_title=name,
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


def _check_geoserver_store(store_name, dataset_type, overwrite):
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
                    _log("Deleting previously existing store")
                    store.delete()
                else:
                    raise GeoNodeException(_("Dataset already exists"))
            else:
                for resource in resources:
                    if resource.name == store_name:
                        if not overwrite:
                            raise GeoNodeException(
                                _("Name already in use and overwrite is False"))
                        existing_type = resource.resource_type or resource.polymorphic_ctype.name
                        if existing_type != dataset_type:
                            msg = (f"Type of uploaded file {store_name} ({dataset_type}) does not "
                                   "match type of existing resource type "
                                   f"{existing_type}")
                            _log(msg)
                            raise GeoNodeException(msg)


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
                        [f.file_type.dataset_type == 'coverage' for f in spatial_files]):
                    msg = "Please upload only one type of file at a time"
                    logger.exception(Exception(msg))
                    raise GeneralUploadException(detail=msg)
            name = get_valid_dataset_name(layer, overwrite)
            _log(f'Name for layer: {name}')
            if not any(spatial_files.all_files()):
                msg = "Unable to recognize the uploaded file(s)"
                logger.exception(Exception(msg))
                raise GeneralUploadException(detail=msg)
            the_dataset_type = get_dataset_type(spatial_files)
            _check_geoserver_store(name, the_dataset_type, overwrite)
            if the_dataset_type not in (
                    FeatureType.resource_type,
                    Coverage.resource_type):
                msg = f"Expected layer type to FeatureType or Coverage, not {the_dataset_type}"
                logger.exception(Exception(msg))
                raise GeneralUploadException(msg)
            files_to_upload = preprocess_files(spatial_files)
            _log(f"files_to_upload: {files_to_upload}")
            _log(f'Uploading {the_dataset_type}')
            error_msg = None
            try:
                upload = None
                if Upload.objects.filter(user=user, name=name).exists():
                    upload = Upload.objects.filter(user=user, name=name).order_by('-date').first()
                if upload:
                    if upload.state == enumerations.STATE_READY:
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
                        state=enumerations.STATE_READY,
                        upload_dir=spatial_files.dirname
                    )
                    upload.store_spatial_files = store_spatial_files

                    # @todo settings for use_url or auto detection if geoserver is
                    # on same host

                    # Is it a regular file or an ImageMosaic?
                    # if mosaic_time_regex and mosaic_time_value:
                    if mosaic:  # we want to ingest as ImageMosaic
                        target_store, files_to_upload = utils.import_imagemosaic_granules(
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
                    upload.set_processing_state(enumerations.STATE_INVALID)

                # @todo once the random tmp9723481758915 type of name is not
                # around, need to track the name computed above, for now, the
                # target store name can be used
            except Exception as e:
                logger.exception(e)
                raise e

            if error_msg:
                logger.exception(Exception(error_msg))
                raise GeneralUploadException(detail=error_msg)
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
        _log(f'Setting transforms {transforms}')
        import_session.tasks[0].add_transforms(transforms)
        try:
            upload_session.time_transforms = transforms
            upload_session.time = True
        except gsimporter.BadRequest as br:
            logger.exception(br)
            Upload.objects.invalidate_from_session(upload_session)
            raise GeneralUploadException(detail=_('Error configuring time: ') + br)
        import_session.tasks[0].save_transforms()
    else:
        upload_session.time = False
    try:
        import_session = import_session.reload()
    except gsimporter.api.NotFound as e:
        logger.exception(e)
        Upload.objects.invalidate_from_session(upload_session)
        raise GeneralUploadException(detail=_("The GeoServer Import Session is no more available ") + str(e))
    upload_session.import_session = import_session
    upload_session = Upload.objects.update_from_session(upload_session)


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
        raise GeneralUploadException(detail=_("The GeoServer Import Session is no more available ") + str(e))
    upload_session.import_session = import_session
    upload_session = Upload.objects.update_from_session(upload_session)


def srs_step(upload_session, source, target):
    import_session = upload_session.import_session
    task = import_session.tasks[0]
    if source:
        _log('Setting SRS to %s', source)
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
        raise GeneralUploadException(detail=_("The GeoServer Import Session is no more available ") + str(e))
    upload_session.import_session = import_session
    upload_session = Upload.objects.update_from_session(upload_session)


def final_step(upload_session, user, charset="UTF-8", dataset_id=None):
    import_session = upload_session.import_session
    if import_session:
        import_id = import_session.id
        saved_dataset = None
        lock_id = f'final_step-{import_id}'
        with AcquireLock(lock_id, blocking=True) as lock:
            if lock.acquire() is True:
                _upload = None
                try:
                    _upload = Upload.objects.get(import_id=import_id)
                    saved_dataset = _upload.resource
                except Exception as e:
                    logger.exception(e)
                    Upload.objects.invalidate_from_session(upload_session)
                    raise GeneralUploadException(detail=_("The Upload Session is no more available ") + str(e))

                _log(f'Reloading session {import_id} to check validity')
                try:
                    import_session = gs_uploader.get_session(import_id)
                except gsimporter.api.NotFound as e:
                    logger.exception(e)
                    Upload.objects.invalidate_from_session(upload_session)
                    raise GeneralUploadException(detail=_("The GeoServer Import Session is no more available ") + str(e))

                if import_session.tasks is None or len(import_session.tasks) == 0:
                    return saved_dataset

                task = import_session.tasks[0]
                try:
                    if charset:
                        task.set_charset(charset)
                except Exception as e:
                    logger.exception(e)

                # @todo see above in save_step, regarding computed unique name
                name = task.layer.name
                target = task.target
                has_time = False
                if upload_session.time and upload_session.time_info and upload_session.time_transforms:
                    has_time = True

                _vals = dict(
                    title=upload_session.dataset_title,
                    abstract=upload_session.dataset_abstract,
                    alternate=task.get_target_layer_name(),
                    store=target.name,
                    name=task.layer.name,
                    workspace=target.workspace_name,
                    subtype=get_dataset_storetype(target.store_type) if not has_time else get_dataset_storetype('vectorTimeSeries')
                )

                if saved_dataset:
                    name = saved_dataset.get_real_instance().name

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

                if not saved_dataset and not (_tasks_failed or _tasks_waiting) and (
                        import_session.state == enumerations.STATE_READY or (import_session.state == enumerations.STATE_PENDING and _tasks_ready)):
                    _log(f"final_step: Running Import Session {import_session.id} - target: {target.name} - alternate: {task.get_target_layer_name()}")
                    _log(f" -- session state: {import_session.state} - task state: {task.state}")

                    utils.run_import(upload_session, async_upload=False)

                    import_session = import_session.reload()
                    task = import_session.tasks[0]
                    name = task.layer.name
                    target = task.target
                    _vals['store'] = target.name
                    _vals['name'] = task.layer.name
                    _vals['workspace'] = target.workspace_name
                    _vals['alternate'] = task.get_target_layer_name()
                elif import_session.state == enumerations.STATE_INCOMPLETE and _tasks_failed:
                    Upload.objects.invalidate_from_session(upload_session)
                    raise GeneralUploadException(detail=f'Unknown Session task state: {task.state}')
                try:
                    import_session = gs_uploader.get_session(import_id)
                except gsimporter.api.NotFound as e:
                    logger.exception(e)
                    Upload.objects.invalidate_from_session(upload_session)
                    raise GeneralUploadException(detail=_("The GeoServer Import Session is no more available ") + str(e))

                upload_session.import_session = import_session.reload()
                upload_session = Upload.objects.update_from_session(upload_session, resource=saved_dataset)

                _tasks_failed = any([_task.state in ["BAD_FORMAT", "ERROR", "CANCELED"] for _task in import_session.tasks])
                _tasks_waiting = any([_task.state in ["NO_CRS", "NO_BOUNDS", "NO_FORMAT"] for _task in import_session.tasks])

                if import_session.state != enumerations.STATE_COMPLETE or _tasks_waiting or _tasks_failed:
                    if import_session.state == enumerations.STATE_PENDING and _tasks_waiting:
                        if any([_task.state == "NO_CRS" for _task in import_session.tasks]):
                            _redirect_to = f"/upload/srs?id={import_session.id}"
                            _upload.set_resume_url(_redirect_to)
                            _upload.set_processing_state(enumerations.STATE_WAITING)
                        elif _tasks_failed:
                            _upload.set_processing_state(enumerations.STATE_INVALID)
                    return None

                _log(f'Creating Django record for [{name}]')
                if Upload.objects.filter(import_id=import_id).exists():
                    if Upload.objects.filter(import_id=import_id).count() > 1:
                        Upload.objects.invalidate_from_session(upload_session)
                        _cause = f'More than Upload Session associated to the Importer ID {import_id}'
                        raise GeneralUploadException(detail=f"Import Session failed.{str(_cause)}")
                    saved_dataset = Upload.objects.filter(import_id=import_id).get().resource

                dataset_uuid = None

                if saved_dataset:
                    _vals['name'] = saved_dataset.get_real_instance().name
                    _log(f'Django record for [{saved_dataset.get_real_instance().name}] already exists, updating with vals: {_vals}')
                    return resource_manager.update(
                        saved_dataset.uuid,
                        instance=saved_dataset,
                        vals=_vals)
                else:
                    _log(f'Django record for [{name}] does not exist, creating with vals: {_vals}')

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
                            dataset_uuid, vals, regions, keywords, custom = parse_metadata(
                                open(xml_file).read())
                            metadata_uploaded = True
                            _vals.update(vals)
                    except Exception as e:
                        Upload.objects.invalidate_from_session(upload_session)
                        logger.exception(e)
                        raise GeneralUploadException(detail=_("Exception occurred while parsing the provided Metadata file.") + str(e))

                # look for SLD
                sld_file = upload_session.base_file[0].sld_files
                sld_uploaded = False
                if sld_file:
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
                            raise GeneralUploadException(detail=_('Error uploading Dataset') + str(e))
                    sld_uploaded = True
                else:
                    # get_files will not find the sld if it doesn't match the base name
                    # so we've worked around that in the view - if provided, it will be here
                    if upload_session.import_sld_file:
                        _log('using provided sld file from importer')
                        base_file = upload_session.base_file
                        sld_file = base_file[0].sld_files[0]
                    sld_uploaded = False
                _log(f'[sld_uploaded: {sld_uploaded}] sld_file: {sld_file}')

                # Make sure the layer does not exists already
                if dataset_uuid and Dataset.objects.filter(uuid=dataset_uuid).count():
                    Upload.objects.invalidate_from_session(upload_session)
                    _log("The UUID identifier from the XML Metadata is already in use in this system.")
                    raise GeneralUploadException(detail=_("The UUID identifier from the XML Metadata is already in use in this system."))

                # Is it a regular file or an ImageMosaic?
                is_mosaic = False
                has_time = has_elevation = False
                start = end = None
                if upload_session.mosaic_time_regex and upload_session.mosaic_time_value:
                    has_time = True
                    is_mosaic = True
                    start = datetime.datetime.strptime(upload_session.mosaic_time_value,
                                                       TIME_REGEX_FORMAT[upload_session.mosaic_time_regex])
                    start = pytz.utc.localize(start, is_dst=False)
                    end = start
                if upload_session.time and upload_session.time_info and upload_session.time_transforms:
                    has_time = True

                if upload_session.append_to_mosaic_opts:
                    # Is it a mosaic or a granule that must be added to an Image Mosaic?
                    saved_dataset_filter = Dataset.objects.filter(
                        name=upload_session.append_to_mosaic_name)
                    if not saved_dataset_filter.exists():
                        try:
                            saved_dataset = resource_manager.create(
                                dataset_uuid,
                                resource_type=Dataset,
                                defaults=dict(
                                    dirty_state=True,
                                    state=enumerations.STATE_READY,
                                    store=_vals.get('store'),
                                    workspace=_vals.get('workspace'),
                                    name=upload_session.append_to_mosaic_name))
                            created = True
                        except IntegrityError as e:
                            logger.exception(e)
                            raise GeneralUploadException(detail=f"There's an incosistent Datasets on the DB for {task.layer.name}{str(e)}")
                    elif saved_dataset_filter.count() == 1:
                        saved_dataset = saved_dataset_filter.get()
                        created = False
                    else:
                        raise GeneralUploadException(detail=f"There's an incosistent number of Datasets on the DB for {upload_session.append_to_mosaic_name}")
                    saved_dataset.set_dirty_state()
                    if saved_dataset.temporal_extent_start and end:
                        if pytz.utc.localize(
                                saved_dataset.temporal_extent_start,
                                is_dst=False) < end:
                            saved_dataset.temporal_extent_end = end
                            Dataset.objects.filter(
                                name=upload_session.append_to_mosaic_name).update(
                                temporal_extent_end=end)
                        else:
                            saved_dataset.temporal_extent_start = end
                            Dataset.objects.filter(
                                name=upload_session.append_to_mosaic_name).update(
                                temporal_extent_start=end)
                else:
                    # The dataset is a standard one, no mosaic options enabled...
                    saved_dataset_filter = Dataset.objects.filter(
                        store=_vals.get('store'),
                        workspace=_vals.get('workspace'),
                        name=_vals.get('name'))
                    if not saved_dataset_filter.exists():
                        try:
                            files_list = []
                            if upload_session.spatial_files_uploaded:
                                files_list.append(upload_session.base_file.data[0].base_file)
                                files_list.extend(upload_session.base_file.data[0].auxillary_files)
                                files_list.extend(upload_session.base_file.data[0].sld_files)
                                files_list.extend(upload_session.base_file.data[0].xml_files)
                            saved_dataset = resource_manager.create(
                                dataset_uuid,
                                resource_type=Dataset,
                                defaults=dict(
                                    store=_vals.get('store'),
                                    subtype=_vals.get('subtype'),
                                    alternate=_vals.get('alternate'),
                                    workspace=_vals.get('workspace'),
                                    title=_vals.get('title'),
                                    name=_vals.get('name'),
                                    abstract=_vals.get('abstract', _('No abstract provided')),
                                    owner=user,
                                    dirty_state=True,
                                    state=enumerations.STATE_READY,
                                    temporal_extent_start=start,
                                    temporal_extent_end=end,
                                    is_mosaic=is_mosaic,
                                    has_time=has_time,
                                    has_elevation=has_elevation,
                                    files=files_list,
                                    time_regex=upload_session.mosaic_time_regex))
                            created = True
                        except IntegrityError as e:
                            logger.exception(e)
                            raise GeneralUploadException(detail=f"There's an incosistent Datasets on the DB for {task.layer.name}{str(e)}")
                    elif saved_dataset_filter.count() == 1:
                        saved_dataset = saved_dataset_filter.get()
                        created = False
                    else:
                        raise GeneralUploadException(detail=f"There's an incosistent number of Datasets on the DB for {task.layer.name}")

                assert saved_dataset

                # Hide the dataset until the upload process finishes...
                saved_dataset.set_processing_state(enumerations.STATE_RUNNING)
                saved_dataset.set_dirty_state()
                _log(f" -- Finalizing Upload for {saved_dataset}... {saved_dataset.state}")

                # Update the state from session...
                upload_session = Upload.objects.update_from_session(upload_session, resource=saved_dataset)

                # Finalize the upload...
                # Set default permissions on the newly created layer and send notifications
                permissions = upload_session.permissions

                # Finalize Upload
                try:
                    with transaction.atomic():
                        resource_manager.set_permissions(
                            None, instance=saved_dataset, permissions=permissions, created=created)
                        resource_manager.exec(
                            'set_time_info', None, instance=saved_dataset, time_info=upload_session.time_info)
                        saved_dataset.refresh_from_db()
                        resource_manager.update(
                            None, instance=saved_dataset, xml_file=xml_file, metadata_uploaded=metadata_uploaded)
                        resource_manager.exec(
                            'set_style', None, instance=saved_dataset, sld_uploaded=sld_uploaded, sld_file=sld_file, tempdir=upload_session.tempdir)
                        resource_manager.set_thumbnail(
                            None, instance=saved_dataset)

                        Upload.objects.filter(resource=saved_dataset).update(complete=True)
                        [u.set_processing_state(enumerations.STATE_PROCESSED) for u in Upload.objects.filter(resource=saved_dataset)]
                except Exception as e:
                    logger.exception(e)
                    Upload.objects.filter(resource=saved_dataset).update(complete=False)
                    [u.set_processing_state(enumerations.STATE_INVALID) for u in Upload.objects.filter(resource=saved_dataset)]
                finally:
                    _log(f" -- Upload completed for {saved_dataset}... {saved_dataset.state}")

    return saved_dataset
