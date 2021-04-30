# -*- coding: utf-8 -*-
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

import uuid
import logging
import os.path
import zipfile
import traceback

from django.conf import settings
from django.db.models import Max
from django.core.files import File
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

import geoserver
from geoserver.resource import Coverage
from geoserver.resource import FeatureType
from gsimporter import BadRequest

from geonode import GeoNodeException
from geonode.upload import UploadException, LayerNotReady

from ..people.utils import get_default_user
from ..layers.models import Layer, UploadSession
from ..layers.utils import get_valid_layer_name
from ..geoserver.tasks import (
    # geoserver_set_style,
    # geoserver_create_style,
    geoserver_finalize_upload
)
from ..geoserver.helpers import (
    set_time_info,
    gs_catalog,
    gs_uploader
)
from . import utils
from .models import Upload
from .upload_preprocessing import preprocess_files

logger = logging.getLogger(__name__)


def _log(msg, *args):
    logger.debug(msg, *args)


class UploaderSession(object):

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
    import_session = save_step(
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
    time_step(upload_session,
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
                    raise GeoNodeException("Layer already exists")
            else:
                for resource in resources:
                    if resource.name == store_name:
                        if not overwrite:
                            raise GeoNodeException(
                                "Name already in use and overwrite is False")
                        existing_type = resource.resource_type
                        if existing_type != layer_type:
                            msg = (f"Type of uploaded file {store_name} ({layer_type}) does not "
                                   f"match type of existing resource type {existing_type}")
                            logger.error(msg)
                            raise GeoNodeException(msg)


def _get_layer_type(spatial_files):
    if spatial_files.archive is not None:
        the_layer_type = FeatureType.resource_type
    else:
        the_layer_type = spatial_files[0].file_type.layer_type
    return the_layer_type


def save_step(user, layer, spatial_files, overwrite=True, mosaic=False,
              append_to_mosaic_opts=None, append_to_mosaic_name=None,
              mosaic_time_regex=None, mosaic_time_value=None,
              time_presentation=None, time_presentation_res=None,
              time_presentation_default_value=None,
              time_presentation_reference_value=None,
              charset_encoding="UTF-8"):
    logger.debug(
        f'Uploading layer: {layer}, files {spatial_files!r}')
    if len(spatial_files) > 1:
        # we only support more than one file if they're rasters for mosaicing
        if not all(
                [f.file_type.layer_type == 'coverage' for f in spatial_files]):
            raise UploadException(
                "Please upload only one type of file at a time")
    name = get_valid_layer_name(layer, overwrite)
    logger.debug(f'Name for layer: {name!r}')
    if not any(spatial_files.all_files()):
        raise UploadException("Unable to recognize the uploaded file(s)")
    the_layer_type = _get_layer_type(spatial_files)
    _check_geoserver_store(name, the_layer_type, overwrite)
    if the_layer_type not in (
            FeatureType.resource_type,
            Coverage.resource_type):
        raise RuntimeError(f"Expected layer type to FeatureType or Coverage, not {the_layer_type}")
    files_to_upload = preprocess_files(spatial_files)
    logger.debug(f"files_to_upload: {files_to_upload}")
    logger.debug(f'Uploading {the_layer_type}')
    error_msg = None
    try:
        next_id = _get_next_id()
        # Truncate name to maximum length defined by the field.
        max_length = Upload._meta.get_field('name').max_length
        name = name[:max_length]
        # save record of this whether valid or not - will help w/ debugging
        upload, _ = Upload.objects.get_or_create(
            user=user,
            name=name,
            state=Upload.STATE_INVALID,
            upload_dir=spatial_files.dirname
        )

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
                target_store=None,
                charset_encoding=charset_encoding
            )
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
            upload.state = upload.STATE_INVALID
            upload.save()

        # @todo once the random tmp9723481758915 type of name is not
        # around, need to track the name computed above, for now, the
        # target store name can be used
    except Exception as e:
        tb = traceback.format_exc()
        logger.debug(tb)
        logger.exception('Error creating import session')
        raise e

    if error_msg:
        raise UploadException(error_msg)
    else:
        _log("Finished upload of [%s] to GeoServer without errors.", name)

    return import_session


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
        upload_session.import_session.tasks[0].remove_transforms(
            upload_session.time_transforms
        )

    if transforms:
        logger.debug(f'Setting transforms {transforms}')
        upload_session.import_session.tasks[0].add_transforms(transforms)
        try:
            upload_session.time_transforms = transforms
            upload_session.time = True
        except BadRequest as br:
            raise UploadException.from_exc('Error configuring time:', br)
        upload_session.import_session.tasks[0].save_transforms()
    else:
        upload_session.time = False


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
    import_session = import_session.reload()
    upload_session.import_session = import_session


def srs_step(upload_session, source, target):
    import_session = upload_session.import_session
    task = import_session.tasks[0]
    if source:
        logger.debug('Setting SRS to %s', source)
        task.set_srs(source)

    transform = {'type': 'ReprojectTransform',
                 'source': source,
                 'target': target,
                 }
    task.remove_transforms([transform], by_field='type', save=False)
    task.add_transforms([transform], save=False)
    task.save_transforms()
    import_session = import_session.reload()
    upload_session.import_session = import_session


def final_step(upload_session, user, charset="UTF-8"):
    import_session = upload_session.import_session
    _log('Reloading session %s to check validity', import_session.id)
    import_session = import_session.reload()
    upload_session.import_session = import_session

    # the importer chooses an available featuretype name late in the game need
    # to verify the resource.name otherwise things will fail.  This happens
    # when the same data is uploaded a second time and the default name is
    # chosen
    cat = gs_catalog

    # Create the style and assign it to the created resource
    # FIXME: Put this in gsconfig.py
    task = import_session.tasks[0]
    task.set_charset(charset)

    # @todo see above in save_step, regarding computed unique name
    name = task.layer.name

    _log('Getting from catalog [%s]', name)
    publishing = cat.get_layer(name)

    if import_session.state == 'INCOMPLETE':
        if task.state != 'ERROR':
            raise Exception(f'unknown item state: {task.state}')
    elif import_session.state == 'READY':
        import_session.commit()
    elif import_session.state == 'PENDING':
        if task.state == 'READY':
            # if not task.data.format or task.data.format != 'Shapefile':
            import_session.commit()

    if not publishing:
        raise LayerNotReady(
            f"Expected to find layer named '{name}' in geoserver")

    _log('Creating Django record for [%s]', name)
    target = task.target
    alternate = task.get_target_layer_name()
    layer_uuid = str(uuid.uuid1())
    title = upload_session.layer_title
    abstract = upload_session.layer_abstract

    # Is it a regular file or an ImageMosaic?
    # if upload_session.mosaic_time_regex and upload_session.mosaic_time_value:
    saved_layer = None
    if upload_session.mosaic:
        import pytz
        import datetime
        from geonode.layers.models import TIME_REGEX_FORMAT

        # llbbox = publishing.resource.latlon_bbox
        start = None
        end = None
        if upload_session.mosaic_time_regex and upload_session.mosaic_time_value:
            has_time = True
            start = datetime.datetime.strptime(upload_session.mosaic_time_value,
                                               TIME_REGEX_FORMAT[upload_session.mosaic_time_regex])
            start = pytz.utc.localize(start, is_dst=False)
            end = start
        else:
            has_time = False

        if not upload_session.append_to_mosaic_opts:
            try:
                with transaction.atomic():
                    saved_layer, created = Layer.objects.get_or_create(
                        uuid=layer_uuid,
                        defaults=dict(
                            store=target.name,
                            storeType=target.store_type,
                            alternate=alternate,
                            workspace=target.workspace_name,
                            title=title,
                            name=task.layer.name,
                            abstract=abstract or '',
                            owner=user,
                            temporal_extent_start=start,
                            temporal_extent_end=end,
                            is_mosaic=True,
                            has_time=has_time,
                            has_elevation=False,
                            time_regex=upload_session.mosaic_time_regex)
                    )
            except IntegrityError:
                raise
            assert saved_layer
        else:
            # saved_layer = Layer.objects.filter(name=upload_session.append_to_mosaic_name)
            # created = False
            saved_layer, created = Layer.objects.get_or_create(
                name=upload_session.append_to_mosaic_name)
            assert saved_layer
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
        _has_time = (True if upload_session.time and upload_session.time_info and
                     upload_session.time_transforms else False)
        try:
            with transaction.atomic():
                saved_layer, created = Layer.objects.get_or_create(
                    uuid=layer_uuid,
                    defaults=dict(
                        store=target.name,
                        storeType=target.store_type,
                        alternate=alternate,
                        workspace=target.workspace_name,
                        title=title,
                        name=task.layer.name,
                        abstract=abstract or '',
                        owner=user,
                        has_time=_has_time)
                )
        except IntegrityError:
            raise
        assert saved_layer

    # Create a new upload session
    try:
        with transaction.atomic():
            geonode_upload_session, created = UploadSession.objects.get_or_create(
                resource=saved_layer, user=user
            )
            geonode_upload_session.processed = False
            geonode_upload_session.save()
    except IntegrityError:
        raise

    # Add them to the upload session (new file fields are created).
    assigned_name = None

    def _store_file(saved_layer,
                    geonode_upload_session,
                    base_file,
                    assigned_name,
                    base=False):
        with open(base_file, 'rb') as f:
            file_name, type_name = os.path.splitext(os.path.basename(base_file))
            geonode_upload_session.layerfile_set.create(
                name=file_name,
                base=base,
                file=File(
                    f, name=f'{assigned_name or saved_layer.name}{type_name}'))
            # save the system assigned name for the remaining files
            if not assigned_name:
                the_file = geonode_upload_session.layerfile_set.all()[0].file.name
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

    _log('Creating style for [%s]', name)
    # look for SLD
    sld_file = upload_session.base_file[0].sld_files
    sld_uploaded = False
    if sld_file:
        # If it's contained within a zip, need to extract it
        if upload_session.base_file.archive:
            archive = upload_session.base_file.archive
            zf = zipfile.ZipFile(archive, 'r', allowZip64=True)
            zf.extract(sld_file[0], os.path.dirname(archive))
            # Assign the absolute path to this file
            sld_file[0] = f"{os.path.dirname(archive)}/{sld_file[0]}"
        sld_file = sld_file[0]
        sld_uploaded = True
        # geoserver_set_style.apply_async((saved_layer.id, sld_file))
    else:
        # get_files will not find the sld if it doesn't match the base name
        # so we've worked around that in the view - if provided, it will be here
        if upload_session.import_sld_file:
            _log('using provided sld file')
            base_file = upload_session.base_file
            sld_file = base_file[0].sld_files[0]
        sld_uploaded = False
        # geoserver_create_style.apply_async((saved_layer.id, name, sld_file, upload_session.tempdir))

    # look for xml and finalize Layer metadata
    xml_file = upload_session.base_file[0].xml_files
    if xml_file:
        # get model properties from XML
        # If it's contained within a zip, need to extract it
        if upload_session.base_file.archive:
            archive = upload_session.base_file.archive
            zf = zipfile.ZipFile(archive, 'r', allowZip64=True)
            zf.extract(xml_file[0], os.path.dirname(archive))
            # Assign the absolute path to this file
            xml_file = f"{os.path.dirname(archive)}/{xml_file[0]}"

    if upload_session.time_info:
        set_time_info(saved_layer, **upload_session.time_info)

    # Set default permissions on the newly created layer and send notifications
    permissions = upload_session.permissions
    geoserver_finalize_upload.apply_async(
        (import_session.id, saved_layer.id, permissions, created,
         xml_file, sld_file, sld_uploaded, upload_session.tempdir))

    return saved_layer
