#########################################################################
#
# Copyright (C) 2012 OpenPlans
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
from geonode.layers.utils import get_valid_layer_name
from geonode.layers.metadata import set_metadata
from geonode.layers.models import Layer
from geonode import GeoNodeException
from geonode.people.utils import get_default_user
from geonode.upload.models import Upload
from geonode.upload import signals
from geonode.upload.utils import create_geoserver_db_featurestore
from geonode.geoserver.helpers import gs_catalog, gs_uploader, ogc_server_settings
from geonode.geoserver.helpers import set_time_info

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
           overwrite=False):

    if user is None:
        user = get_default_user()
    if isinstance(user, basestring):
        user = get_user_model().objects.get(username=user)

    import_session = save_step(user, name, base_file, overwrite)

    upload_session = UploaderSession(
        base_file=base_file,
        name=name,
        import_session=import_session,
        layer_abstract="",
        layer_title=name,
        permissions=None
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


def save_step(user, layer, spatial_files, overwrite=True):
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
        next_id = Upload.objects.all().aggregate(Max('import_id')).values()[0]
        next_id = next_id + 1 if next_id else 1

        # save record of this whether valid or not - will help w/ debugging
        upload = Upload.objects.create(
            user=user,
            name=name,
            state=Upload.STATE_INVALID,
            upload_dir=spatial_files.dirname)

        # @todo settings for use_url or auto detection if geoserver is
        # on same host
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
    if import_session.state == 'INCOMPLETE':
        if task.state != 'ERROR':
            raise Exception('unknown item state: %s' % task.state)

    # if a target datastore is configured, ensure the datastore exists
    # in geoserver and set the uploader target appropriately

    if ogc_server_settings.GEOGIG_ENABLED and upload_session.geogig is True \
            and task.target.store_type != 'coverageStore':

        target = create_geoserver_db_featurestore(
            store_type='geogig',
            store_name=upload_session.geogig_store)
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
    
    # check if the task has an error, if it does, present it to the user
    if task.state == 'ERROR':
        raise UploadException(task.get_progress().get('message'))

    # @todo see above in save_step, regarding computed unique name
    name = task.layer.name

    _log('Getting from catalog [%s]', name)
    publishing = cat.get_layer(name)

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

    if sld is not None:
        try:
            cat.create_style(name, sld)
        except geoserver.catalog.ConflictingDataError as e:
            msg = 'There was already a style named %s in GeoServer, cannot overwrite: "%s"' % (
                name, str(e))
            # what are we doing with this var?
            # style = cat.get_style(name)
            logger.warn(msg)
            e.args = (msg,)

        # FIXME: Should we use the fully qualified typename?
        publishing.default_style = cat.get_style(name)
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

    defaults = dict(store=target.name,
                    storeType=target.store_type,
                    typename=typename,
                    workspace=target.workspace_name,
                    title=title,
                    uuid=layer_uuid,
                    abstract=abstract or '',
                    owner=user,)

    _log('record defaults: %s', defaults)
    saved_layer, created = Layer.objects.get_or_create(
        name=task.layer.name,
        defaults=defaults
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
        vals, keywords = set_metadata(open(xml_file[0]).read())

        # set taggit keywords
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
    _log('Setting default permissions for [%s]', name)
    if permissions is not None:
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
