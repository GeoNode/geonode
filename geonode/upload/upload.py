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
from geonode.layers.utils import get_valid_layer_name, resolve_regions
from geonode.layers.metadata import set_metadata
from geonode.layers.models import Layer
from geonode import GeoNodeException
from geonode.people.utils import get_default_user
from geonode.upload.models import Upload
from geonode.upload import signals
from geonode.upload.utils import create_geoserver_db_featurestore
from geonode.geoserver.helpers import gs_catalog, gs_uploader, ogc_server_settings
from geonode.geoserver.helpers import mosaic_delete_first_granule, set_time_dimension, set_time_info

import geoserver
from geoserver.resource import Coverage
from geoserver.resource import FeatureType
from gsimporter import BadRequest

from django.conf import settings
from django.db.models import Max
from django.contrib.auth import get_user_model

import shutil
import os.path
import logging
import uuid
import zipfile

logger = logging.getLogger(__name__)


class UploadException(Exception):

    '''A handled exception meant to be presented to the user'''

    @staticmethod
    def from_exc(msg, ex):
        args = [msg]
        args.extend(ex.args)
        return UploadException(*args)


class LayerNotReady(Exception):
    pass


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

    # blob of permissions JSON
    permissions = None

    # store most recently configured time transforms to support deleting
    time_transforms = None

    # defaults to REPLACE if not provided. Accepts APPEND, too
    update_mode = None

    # Import to GeoGig repository
    geogig = None

    # GeoGig Repository to import to
    geogig_store = None

    # Configure Time for this Layer
    time = None

    # the title given to the layer
    layer_title = None

    # the abstract
    layer_abstract = None

    # track the most recently completed upload step
    completed_step = None

    # the upload type - see the _pages dict in views
    upload_type = None

    # time related info - need to store here until geoserver layer exists
    time_info = None

    # whether the user has selected a time dimension for ImageMosaic granules or not
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
                raise Exception('not handled : %s' % k)

    def cleanup(self):
        """do what we should at the given state of the upload"""
        pass


def upload(name, base_file,
           user=None, time_attribute=None,
           time_transform_type=None,
           end_time_attribute=None, end_time_transform_type=None,
           presentation_strategy=None, precision_value=None,
           precision_step=None, use_big_date=False,
           overwrite=False,
           mosaic=False,
           append_to_mosaic_opts=None, append_to_mosaic_name=None,
           mosaic_time_regex=None, mosaic_time_value=None,
           time_presentation=None, time_presentation_res=None,
           time_presentation_default_value=None, time_presentation_reference_value=None):

    if user is None:
        user = get_default_user()
    if isinstance(user, basestring):
        user = get_user_model().objects.get(username=user)

    import_session = save_step(user, name, base_file, overwrite,
                               mosaic=mosaic,
                               append_to_mosaic_opts=append_to_mosaic_opts, append_to_mosaic_name=append_to_mosaic_name,
                               mosaic_time_regex=mosaic_time_regex, mosaic_time_value=mosaic_time_value,
                               time_presentation=time_presentation, time_presentation_res=time_presentation_res,
                               time_presentation_default_value=time_presentation_default_value,
                               time_presentation_reference_value=time_presentation_reference_value)

    upload_session = UploaderSession(
        base_file=base_file,
        name=name,
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
              time_format=None, srs=None, use_big_date=use_big_date)

    run_import(upload_session, async=False)

    final_step(upload_session, user)


def _log(msg, *args):
    logger.info(msg, *args)


def save_step(user, layer, spatial_files, overwrite=True,
              mosaic=False,
              append_to_mosaic_opts=None, append_to_mosaic_name=None,
              mosaic_time_regex=None, mosaic_time_value=None,
              time_presentation=None, time_presentation_res=None,
              time_presentation_default_value=None, time_presentation_reference_value=None):
    _log('Uploading layer: [%s], files [%s]', layer, spatial_files)

    if len(spatial_files) > 1:
        # we only support more than one file if they're rasters for mosaicing
        if not all(
                [f.file_type.layer_type == 'coverage' for f in spatial_files]):
            raise UploadException(
                "Please upload only one type of file at a time")

    name = get_valid_layer_name(layer, overwrite)
    _log('Name for layer: [%s]', name)

    if not spatial_files:
        raise UploadException("Unable to recognize the uploaded file(s)")

    the_layer_type = spatial_files[0].file_type.layer_type

    # Check if the store exists in geoserver
    try:
        store = gs_catalog.get_store(name)
    except geoserver.catalog.FailedRequestError as e:
        # There is no store, ergo the road is clear
        pass
    else:
        # If we get a store, we do the following:
        resources = store.get_resources()
        # Is it empty?
        if len(resources) == 0:
            # What should we do about that empty store?
            if overwrite:
                # We can just delete it and recreate it later.
                store.delete()
            else:
                msg = (
                    'The layer exists and the overwrite parameter is %s' %
                    overwrite)
                raise GeoNodeException(msg)
        else:

            # If our resource is already configured in the store it
            # needs to have the right resource type

            for resource in resources:
                if resource.name == name:

                    assert overwrite, "Name already in use and overwrite is False"

                    existing_type = resource.resource_type
                    if existing_type != the_layer_type:
                        msg = (
                            'Type of uploaded file %s (%s) does not match type '
                            'of existing resource type %s' %
                            (name, the_layer_type, existing_type))
                        _log(msg)
                        raise GeoNodeException(msg)

    if the_layer_type not in (
            FeatureType.resource_type,
            Coverage.resource_type):
        raise Exception(
            'Expected the layer type to be a FeatureType or Coverage, not %s' %
            the_layer_type)
    _log('Uploading %s', the_layer_type)

    error_msg = None
    try:
        # importer tracks ids by autoincrement but is prone to corruption
        # which potentially may reset the id - hopefully prevent this...
        upload_next_id = Upload.objects.all().aggregate(Max('import_id')).values()[0]
        upload_next_id = upload_next_id if upload_next_id else 0
        # next_id = next_id + 1 if next_id else 1
        importer_sessions = gs_uploader.get_sessions()

        last_importer_session = importer_sessions[len(importer_sessions)-1].id if importer_sessions else 0
        next_id = max(int(last_importer_session), int(upload_next_id)) + 1
        next_id = max(int(last_importer_session), int(upload_next_id)) + 1

        # Truncate name to maximum length defined by the field.
        max_length = Upload._meta.get_field('name').max_length
        name = name[:max_length]

        # save record of this whether valid or not - will help w/ debugging
        upload = Upload.objects.create(
            user=user,
            name=name,
            state=Upload.STATE_INVALID,
            upload_dir=spatial_files.dirname)

        # @todo settings for use_url or auto detection if geoserver is
        # on same host

        # Is it a regular file or an ImageMosaic?
        # if mosaic_time_regex and mosaic_time_value:
        if mosaic:
            # we want to ingest as ImageMosaic
            target_store = import_imagemosaic_granules(spatial_files, append_to_mosaic_opts, append_to_mosaic_name,
                                                       mosaic_time_regex, mosaic_time_value, time_presentation,
                                                       time_presentation_res, time_presentation_default_value,
                                                       time_presentation_reference_value)

            # moving forward with a regular Importer session
            import_session = gs_uploader.upload_files(
                spatial_files.all_files(),
                use_url=False,
                import_id=next_id,
                mosaic=len(spatial_files) > 1,
                target_store=target_store)

            upload.moasic = mosaic
            upload.append_to_mosaic_opts = append_to_mosaic_opts
            upload.append_to_mosaic_name = append_to_mosaic_name
            upload.mosaic_time_regex = mosaic_time_regex
            upload.mosaic_time_value = mosaic_time_value
        else:
            # moving forward with a regular Importer session
            import_session = gs_uploader.upload_files(
                spatial_files.all_files(),
                use_url=False,
                import_id=next_id,
                mosaic=len(spatial_files) > 1)

        upload.import_id = import_session.id
        upload.save()

        # any unrecognized tasks/files must be deleted or we can't proceed
        import_session.delete_unrecognized_tasks()

        if not import_session.tasks:
            error_msg = 'No valid upload files could be found'
        elif import_session.tasks[0].state == 'NO_FORMAT':
            error_msg = 'There may be a problem with the data provided - ' \
                        'we could not identify it'

        if len(import_session.tasks) > 1:
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
        logger.exception('Error creating import session')
        raise e

    if error_msg:
        raise UploadException(error_msg)
    else:
        _log("Finished upload of [%s] to GeoServer without errors.", name)

    return import_session


def run_import(upload_session, async):
    """Run the import, possibly asynchronously.

    Returns the target datastore.
    """
    import_session = upload_session.import_session
    import_session = gs_uploader.get_session(import_session.id)
    task = import_session.tasks[0]
    import_execution_requested = False
    if import_session.state == 'INCOMPLETE':
        if task.state != 'ERROR':
            raise Exception('unknown item state: %s' % task.state)
    elif import_session.state == 'PENDING' and task.target.store_type == 'coverageStore':
        if task.state == 'READY':
            import_session.commit(async)
            import_execution_requested = True

    # if a target datastore is configured, ensure the datastore exists
    # in geoserver and set the uploader target appropriately

    if ogc_server_settings.GEOGIG_ENABLED and upload_session.geogig is True \
            and task.target.store_type != 'coverageStore':
        target = create_geoserver_db_featurestore(
            store_type='geogig',
            store_name=upload_session.geogig_store,
            author_name=upload_session.user.username,
            author_email=upload_session.user.email)
        _log(
            'setting target datastore %s %s',
            target.name,
            target.workspace.name)
        task.set_target(target.name, target.workspace.name)

    elif ogc_server_settings.datastore_db and task.target.store_type != 'coverageStore':
        target = create_geoserver_db_featurestore()
        _log(
            'setting target datastore %s %s',
            target.name,
            target.workspace.name)
        task.set_target(target.name, target.workspace.name)
    else:
        target = task.target

    if upload_session.update_mode:
        _log('setting updateMode to %s', upload_session.update_mode)
        task.set_update_mode(upload_session.update_mode)

    _log('running import session')
    # run async if using a database
    if not import_execution_requested:
        import_session.commit(async)

    # @todo check status of import session - it may fail, but due to protocol,
    # this will not be reported during the commit
    return target


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

    def build_time_transform(att, type, format):
        trans = {'type': type, 'field': att}
        if format:
            trans['format'] = format
        return trans

    def build_att_remap_transform(att):
        # @todo the target is so ugly it should be obvious
        return {'type': 'AttributeRemapTransform',
                'field': att,
                'target': 'org.geotools.data.postgis.PostGISDialect$XDate'}

    use_big_date = getattr(settings, 'USE_BIG_DATE', False) and not upload_session.geogig

    if time_attribute:
        if time_transform_type:

            transforms.append(
                build_time_transform(
                    time_attribute,
                    time_transform_type, time_format
                )
            )

        if end_time_attribute and end_time_transform_type:

            transforms.append(
                build_time_transform(
                    end_time_attribute,
                    end_time_transform_type, end_time_format
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
        logger.info('Setting transforms %s' % transforms)
        upload_session.import_session.tasks[0].add_transforms(transforms)
        try:
            upload_session.time_transforms = transforms
        except BadRequest as br:
            raise UploadException.from_exc('Error configuring time:', br)
        upload_session.import_session.tasks[0].save_transforms()


def csv_step(upload_session, lat_field, lng_field):
    import_session = upload_session.import_session
    task = import_session.tasks[0]
    transform = {'type': 'AttributesToPointGeometryTransform',
                 'latField': lat_field,
                 'lngField': lng_field,
                 }
    task.layer.set_srs('EPSG:4326')
    task.remove_transforms([transform], by_field='type', save=False)
    task.add_transforms([transform], save=False)
    task.save_transforms()


def srs_step(upload_session, srs):
    layer = upload_session.import_session.tasks[0].layer
    srs = srs.strip().upper()
    if not srs.startswith("EPSG:"):
        srs = "EPSG:%s" % srs
    logger.info('Setting SRS to %s', srs)
    layer.set_srs(srs)


def final_step(upload_session, user):
    from geonode.geoserver.helpers import get_sld_for
    import_session = upload_session.import_session
    _log('Reloading session %s to check validity', import_session.id)
    import_session = import_session.reload()
    upload_session.import_session = import_session

    # the importer chooses an available featuretype name late in the game need
    # to verify the resource.name otherwise things will fail.  This happens
    # when the same data is uploaded a second time and the default name is
    # chosen

    cat = gs_catalog
    cat._cache.clear()

    # Create the style and assign it to the created resource
    # FIXME: Put this in gsconfig.py

    task = import_session.tasks[0]

    # @todo see above in save_step, regarding computed unique name
    name = task.layer.name

    _log('Getting from catalog [%s]', name)
    publishing = cat.get_layer(name)

    if import_session.state == 'INCOMPLETE':
        if task.state != 'ERROR':
            raise Exception('unknown item state: %s' % task.state)
    elif import_session.state == 'PENDING':
        if task.state == 'READY' and task.data.format != 'Shapefile':
            import_session.commit()

    if not publishing:
        raise LayerNotReady("Expected to find layer named '%s' in geoserver" % name)

    _log('Creating style for [%s]', name)
    # get_files will not find the sld if it doesn't match the base name
    # so we've worked around that in the view - if provided, it will be here
    if upload_session.import_sld_file:
        _log('using provided sld file')
        base_file = upload_session.base_file
        sld_file = base_file[0].sld_files[0]

        f = open(sld_file, 'r')
        sld = f.read()
        f.close()
    else:
        sld = get_sld_for(publishing)

    style = None
    print " **************************************** "
    if sld is not None:
        try:
            cat.create_style(name, sld)
            style = cat.get_style(name)
        except geoserver.catalog.ConflictingDataError as e:
            msg = 'There was already a style named %s in GeoServer, try using another name: "%s"' % (
                name, str(e))
            try:
                cat.create_style(name + '_layer', sld)
                style = cat.get_style(name + '_layer')
            except geoserver.catalog.ConflictingDataError as e:
                msg = 'There was already a style named %s in GeoServer, cannot overwrite: "%s"' % (
                    name, str(e))
                logger.error(msg)
                e.args = (msg,)

                # what are we doing with this var?
                msg = 'No style could be created for the layer, falling back to POINT default one'
                style = cat.get_style('point')
                logger.warn(msg)
                e.args = (msg,)

        # FIXME: Should we use the fully qualified typename?
        publishing.default_style = style
        _log('default style set to %s', name)
        cat.save(publishing)

    _log('Creating Django record for [%s]', name)
    target = task.target
    typename = task.get_target_layer_name()
    layer_uuid = str(uuid.uuid1())

    title = upload_session.layer_title
    abstract = upload_session.layer_abstract

    # @todo hacking - any cached layers might cause problems (maybe
    # delete hook on layer should fix this?)
    cat._cache.clear()

    # Is it a regular file or an ImageMosaic?
    # if upload_session.mosaic_time_regex and upload_session.mosaic_time_value:
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
            saved_layer, created = Layer.objects.get_or_create(
                name=task.layer.name,
                defaults=dict(store=target.name,
                              storeType=target.store_type,
                              typename=typename,
                              workspace=target.workspace_name,
                              title=title,
                              uuid=layer_uuid,
                              abstract=abstract or '',
                              owner=user,),
                temporal_extent_start=start,
                temporal_extent_end=end,
                is_mosaic=True,
                has_time=has_time,
                has_elevation=False,
                time_regex=upload_session.mosaic_time_regex
            )
        else:
            # saved_layer = Layer.objects.filter(name=upload_session.append_to_mosaic_name)
            # created = False
            saved_layer, created = Layer.objects.get_or_create(name=upload_session.append_to_mosaic_name)
            try:
                if saved_layer.temporal_extent_start and end:
                    if pytz.utc.localize(saved_layer.temporal_extent_start, is_dst=False) < end:
                        saved_layer.temporal_extent_end = end
                        Layer.objects.filter(name=upload_session.append_to_mosaic_name).update(
                            temporal_extent_end=end)
                    else:
                        saved_layer.temporal_extent_start = end
                        Layer.objects.filter(name=upload_session.append_to_mosaic_name).update(
                            temporal_extent_start=end)
            except Exception as e:
                _log('There was an error updating the mosaic temporal extent: ' + str(e))
    else:
        saved_layer, created = Layer.objects.get_or_create(
            name=task.layer.name,
            defaults=dict(store=target.name,
                          storeType=target.store_type,
                          typename=typename,
                          workspace=target.workspace_name,
                          title=title,
                          uuid=layer_uuid,
                          abstract=abstract or '',
                          owner=user,)
        )

    # Should we throw a clearer error here?
    assert saved_layer is not None

    # @todo if layer was not created, need to ensure upload target is
    # same as existing target

    _log('layer was created : %s', created)

    if created:
        saved_layer.set_default_permissions()

    # Create the points of contact records for the layer
    _log('Creating points of contact records for [%s]', name)
    saved_layer.poc = user
    saved_layer.metadata_author = user

    # look for xml
    xml_file = upload_session.base_file[0].xml_files
    if xml_file:
        saved_layer.metadata_uploaded = True
        # get model properties from XML
        # If it's contained within a zip, need to extract it
        if upload_session.base_file.archive:
            archive = upload_session.base_file.archive
            zf = zipfile.ZipFile(archive, 'r')
            zf.extract(xml_file[0], os.path.dirname(archive))
            # Assign the absolute path to this file
            xml_file[0] = os.path.dirname(archive) + '/' + xml_file[0]
        identifier, vals, regions, keywords = set_metadata(open(xml_file[0]).read())

        regions_resolved, regions_unresolved = resolve_regions(regions)
        keywords.extend(regions_unresolved)

        # set regions
        regions_resolved = list(set(regions_resolved))
        if regions:
            if len(regions) > 0:
                saved_layer.regions.add(*regions_resolved)

        # set taggit keywords
        keywords = list(set(keywords))
        saved_layer.keywords.add(*keywords)

        # set model properties
        for (key, value) in vals.items():
            if key == "spatial_representation_type":
                # value = SpatialRepresentationType.objects.get(identifier=value)
                pass
            else:
                setattr(saved_layer, key, value)

        saved_layer.save()

    # Set default permissions on the newly created layer
    # FIXME: Do this as part of the post_save hook

    permissions = upload_session.permissions
    if created and permissions is not None:
        _log('Setting default permissions for [%s]', name)
        saved_layer.set_permissions(permissions)

    if upload_session.tempdir and os.path.exists(upload_session.tempdir):
        shutil.rmtree(upload_session.tempdir)

    upload = Upload.objects.get(import_id=import_session.id)
    upload.layer = saved_layer
    upload.complete = True
    upload.save()

    if upload_session.time_info:
        set_time_info(saved_layer, **upload_session.time_info)

    signals.upload_complete.send(sender=final_step, layer=saved_layer)

    return saved_layer


def import_imagemosaic_granules(spatial_files, append_to_mosaic_opts, append_to_mosaic_name,
                                mosaic_time_regex, mosaic_time_value, time_presentation,
                                time_presentation_res, time_presentation_default_value,
                                time_presentation_reference_value):

    # The very first step is to rename the granule by adding the selected regex
    #  matching value to the filename.

    f = spatial_files[0].base_file
    dirname = os.path.dirname(f)
    basename = os.path.basename(f)

    head, tail = os.path.splitext(basename)
    dst_file = os.path.join(dirname, head.replace("_", "-") + "_" + mosaic_time_value + tail)
    os.rename(f, dst_file)
    spatial_files[0].base_file = dst_file

    # We use the GeoServer REST APIs in order to create the ImageMosaic
    #  and later add the granule through the GeoServer Importer.

    # 1. Create a zip file containing the ImageMosaic .properties files
    db = ogc_server_settings.datastore_db
    db_engine = 'postgis' if \
        'postgis' in db['ENGINE'] else db['ENGINE']

    if not db_engine == 'postgis':
        raise UploadException("Unsupported DataBase for Mosaics!")

    context = {
        "abs_path_flag": "True",
        "time_attr":  "time",
        "aux_metadata_flag":  "False",
        "mosaic_time_regex": mosaic_time_regex,
        "db_host": db['HOST'],
        "db_port": db['PORT'],
        "db_name": db['NAME'],
        "db_user": db['USER'],
        "db_password": db['PASSWORD'],
        "db_conn_timeout": db['CONN_TOUT'] or "10",
        "db_conn_min": db['CONN_MIN'] or "1",
        "db_conn_max": db['CONN_MAX'] or "5",
        "db_conn_validate": db['CONN_VALIDATE'] or "true",
    }

    if mosaic_time_regex:
        indexer_template = """AbsolutePath={abs_path_flag}
TimeAttribute={time_attr}
Schema= the_geom:Polygon,location:String,{time_attr}:java.util.Date
PropertyCollectors=TimestampFileNameExtractorSPI[timeregex]({time_attr})
CheckAuxiliaryMetadata={aux_metadata_flag}
SuggestedSPI=it.geosolutions.imageioimpl.plugins.tiff.TIFFImageReaderSpi"""

        timeregex_template = """regex=(?<=_)({mosaic_time_regex})"""

        with open(dirname + '/timeregex.properties', 'w') as timeregex_prop_file:
            timeregex_prop_file.write(timeregex_template.format(**context))

    else:
        indexer_template = """AbsolutePath={abs_path_flag}
Schema= the_geom:Polygon,location:String,{time_attr}
CheckAuxiliaryMetadata={aux_metadata_flag}
SuggestedSPI=it.geosolutions.imageioimpl.plugins.tiff.TIFFImageReaderSpi"""

    datastore_template = """SPI=org.geotools.data.postgis.PostgisNGDataStoreFactory
host={db_host}
port={db_port}
database={db_name}
user={db_user}
passwd={db_password}
Loose\ bbox=true
Estimated\ extends=false
validate\ connections={db_conn_validate}
Connection\ timeout={db_conn_timeout}
min\ connections={db_conn_min}
max\ connections={db_conn_max}"""

    with open(dirname + '/indexer.properties', 'w') as indexer_prop_file:
        indexer_prop_file.write(indexer_template.format(**context))

    with open(dirname + '/datastore.properties', 'w') as datastore_prop_file:
        datastore_prop_file.write(datastore_template.format(**context))

    if not append_to_mosaic_opts:

        z = zipfile.ZipFile(dirname + '/' + head + '.zip', "w")

        z.write(dst_file, arcname=head + "_" + mosaic_time_value + tail)
        z.write(dirname + '/indexer.properties', arcname='indexer.properties')
        z.write(dirname + '/datastore.properties', arcname='datastore.properties')
        if mosaic_time_regex:
            z.write(dirname + '/timeregex.properties', arcname='timeregex.properties')

        z.close()

        # 2. Send a "create ImageMosaic" request to GeoServer through gs_config
        cat = gs_catalog
        cat._cache.clear()
        # - name = name of the ImageMosaic (equal to the base_name)
        # - data = abs path to the zip file
        # - configure = parameter allows for future configuration after harvesting
        name = head
        data = open(dirname + '/' + head + '.zip', 'rb')
        cat.create_imagemosaic(name, data)

        # configure time as LIST
        if mosaic_time_regex:
            set_time_dimension(cat, name, time_presentation, time_presentation_res,
                               time_presentation_default_value, time_presentation_reference_value)

        # - since GeoNode will uploade the first granule again through the Importer, we need to /
        #   delete the one created by the gs_config
        mosaic_delete_first_granule(cat, name)

        return head
    else:
        cat = gs_catalog
        cat._cache.clear()
        cat.reset()
        cat.reload()

        return append_to_mosaic_name
