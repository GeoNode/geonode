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
"_step_view". The goal of seperation of view/logic is to support various
programatic uses of this API. The logic steps should not accept request objects
or return response objects.

State is stored in a UploaderSession object stored in the user's session.
This needs to be made more stateful by adding a model.
"""
from geonode.geoserver.helpers import get_sld_for
from geonode.layers.utils import get_valid_layer_name
from geonode.layers.utils import layer_type
from geonode.layers.metadata import set_metadata
from geonode.layers.models import Layer
from geonode.layers.utils import layer_set_permissions
from geonode.people.models import Profile 
from geonode import GeoNodeException
from geonode.people.utils import get_default_user
from geonode.upload.models import Upload
from geonode.upload import signals
from geonode.upload.utils import create_geoserver_db_featurestore
from geonode.upload.utils import find_file_re
from geonode.upload.utils import gs_uploader

import geoserver
from geoserver.resource import Coverage
from geoserver.resource import FeatureType
from geonode.geoserver.uploader.uploader import BadRequest

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Max

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


class UploaderSession(object):
    """All objects held must be able to surive a good pickling"""

    # the uploader session object
    import_session = None

    # if provided, this file will be uploaded to geoserver and set as
    # the default
    import_sld_file = None

    # location of any temporary uploaded files
    tempdir = None

    #the main uploaded file, zip, shp, tif, etc.
    base_file = None

    #the name to try to give the layer
    name = None

    # blob of permissions JSON
    permissions = None

    form = None  # @todo - needed?

    # defaults to REPLACE if not provided. Accepts APPEND, too
    update_mode = None

    # Import to GeoGit repository
    geogit = None

    # Configure Time for this Layer
    time = None

    # the title given to the layer
    layer_title = None

    # the abstract
    layer_abstract = None

    # computed target (dict since gsconfig objects do not pickle, but
    # attributes matching a datastore) of the import
    import_target = None

    # track the most recently completed upload step
    completed_step = None
    
    # the upload type - see the _pages dict in views
    upload_type = None

    def set_target(self, target):
        self.import_target = {
            'name': target.name,
            'workspace_name': target.workspace.name,
            'resource_type': target.resource_type
        }

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
        user = User.objects.get(username=user)

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

    target = run_import(upload_session, async=False)
    upload_session.set_target(target)
    final_step(upload_session, user)


def _log(msg, *args):
    logger.info(msg, *args)


def save_step(user, layer, base_file, overwrite=True):

    _log('Uploading layer: [%s], base file [%s]', layer, base_file)

    # TODO Add better error handling
    assert os.path.exists(base_file), 'invalid base_file - does not exist'

    name = get_valid_layer_name(layer, overwrite)
    _log('Name for layer: [%s]', name)

    # Step 2. Check that it is uploading to the same resource type as
    # the existing resource

    the_layer_type = layer_type(base_file)

    # Check if the store exists in geoserver
    try:
        store = Layer.objects.gs_catalog.get_store(name)
    except geoserver.catalog.FailedRequestError, e:
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
                msg = ('The layer exists and the overwrite parameter is %s' % overwrite)
                raise GeoNodeException(msg)
        else:

            # If our resource is already configured in the store it
            # needs to have the right resource type

            for resource in resources:
                if resource.name == name:

                    assert overwrite, "Name already in use and overwrite is False"

                    existing_type = resource.resource_type
                    if existing_type != the_layer_type:
                        msg =  ('Type of uploaded file %s (%s) does not match type '
                            'of existing resource type %s' % (name, the_layer_type, existing_type))
                        _log(msg)
                        raise GeoNodeException(msg)

    if the_layer_type not in (FeatureType.resource_type, Coverage.resource_type):
        raise Exception('Expected the layer type to be a FeatureType or Coverage, not %s' % the_layer_type)
    _log('Uploading %s', the_layer_type)

    error_msg = None
    try:
        # importer tracks ids by autoincrement but is prone to corruption
        # which potentially may reset the id - hopefully prevent this...
        next_id = Upload.objects.all().aggregate(Max('import_id')).values()[0]
        next_id = next_id + 1 if next_id else 1

        # @todo settings for use_url or auto detection if geoserver is
        # on same host
        import_session = gs_uploader().upload(
            base_file, use_url=False, import_id=next_id)
            
        # save record of this whether valid or not - will help w/ debugging
        upload = Upload.objects.create_from_session(user, import_session)
        
        if not import_session.tasks:
            error_msg = 'No upload tasks were created'
        elif not import_session.tasks[0].items:
            error_msg = 'No upload items found for task'
            
        if error_msg:
            upload.state = upload.STATE_INVALID
            upload.save()
           
        # @todo once the random tmp9723481758915 type of name is not
        # around, need to track the name computed above, for now, the
        # target store name can be used
    except Exception, e:
        logger.exception('Error creating import session')
        error_msg = str(e)

    if error_msg:
        raise Exception('Could not save the layer %s, there was an upload error: %s' % (name, error_msg))
    else:
        _log("Finished upload of [%s] to GeoServer without errors.", name)

    return import_session


def run_import(upload_session, async):
    """Run the import, possibly asynchronously.

    Returns the target datastore.
    """
    import_session = upload_session.import_session
    import_session = gs_uploader().get_session(import_session.id)
    if import_session.state == 'INCOMPLETE':
        item = upload_session.import_session.tasks[0].items[0]
        if item.state == 'NO_CRS':
            err = 'No projection found'
        else:
            err = item.state or 'Session not ready for import.'
        if err:
            raise Exception(err)

    # if a target datastore is configured, ensure the datastore exists
    # in geoserver and set the uploader target appropriately
    if (hasattr(settings, 'GEOGIT_DATASTORE') and settings.GEOGIT_DATASTORE and
        upload_session.geogit == True and
        import_session.tasks[0].items[0].layer.layer_type != 'RASTER'):
        target = create_geoserver_db_featurestore(type='geogit')
        _log('setting target datastore %s %s',
             target.name, target.workspace.name
            )
        import_session.tasks[0].set_target(
            target.name, target.workspace.name)
    elif (settings.DB_DATASTORE and
        import_session.tasks[0].items[0].layer.layer_type != 'RASTER'):
        target = create_geoserver_db_featurestore(type='postgis')
        _log('setting target datastore %s %s',
             target.name, target.workspace.name
            )
        import_session.tasks[0].set_target(
            target.name, target.workspace.name)
    else:
        target = import_session.tasks[0].target

    if upload_session.update_mode:
        _log('setting updateMode to %s', upload_session.update_mode)
        import_session.tasks[0].set_update_mode(upload_session.update_mode)

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
              time_format=None,
              use_big_date=None):
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
    resource = upload_session.import_session.tasks[0].items[0].resource
    transforms = []

    def build_time_transform(att, type, format):
        trans = {'type': type, 'field': att}
        if format: trans['format'] = format
        return trans

    def build_att_remap_transform(att):
        # @todo the target is so ugly it should be obvious
        return {'type': 'AttributeRemapTransform',
                'field': att,
                'target': 'org.geotools.data.postgis.PostGISDialect$XDate'}
    if use_big_date is None:
        try:
            use_big_date = settings.USE_BIG_DATE
        except:
            use_big_date = False
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
        resource.add_time_dimension_info(
            time_attribute,
            end_time_attribute,
            presentation_strategy,
            precision_value,
            precision_step,
        )
        logger.info('Setting time dimension info')
        resource.save()

    if transforms:
        logger.info('Setting transforms %s' % transforms)
        upload_session.import_session.tasks[0].items[0].add_transforms(transforms)
        try:
            upload_session.import_session.tasks[0].items[0].save()
        except BadRequest, br:
            raise UploadException.from_exc('Error configuring time:',br)


def csv_step(upload_session, lat_field, lng_field):
    import_session = upload_session.import_session
    item = import_session.tasks[0].items[0]
    feature_type = item.resource
    transform = {'type': 'AttributesToPointGeometryTransform',
                 'latField': lat_field,
                 'lngField': lng_field,
                 }
    feature_type.set_srs('EPSG:4326')
    item.add_transforms([transform])
    item.save()


def srs_step(upload_session, srs):
    resource = upload_session.import_session.tasks[0].items[0].resource
    srs = srs.strip().upper()
    if not srs.startswith("EPSG:"):
        srs = "EPSG:%s" % srs
    logger.info('Setting SRS to %s', srs)
    resource.set_srs(srs)


def final_step(upload_session, user):
    import_session = upload_session.import_session
    _log('Reloading session %s to check validity', import_session.id)
    import_session = import_session.reload()
    upload_session.import_session = import_session

    # the importer chooses an available featuretype name late in the game need
    # to verify the resource.name otherwise things will fail.  This happens
    # when the same data is uploaded a second time and the default name is
    # chosen

    cat = Layer.objects.gs_catalog
    cat._cache.clear()

    # Create the style and assign it to the created resource
    # FIXME: Put this in gsconfig.py

    # @todo see above in save_step, regarding computed unique name
    name = import_session.tasks[0].items[0].layer.name

    import time
    time.sleep(4)
    _log('Creating style for [%s]', name)
    publishing = cat.get_layer(name)
    if publishing is None:
        raise Exception("Expected to find layer named '%s' in geoserver", name)

    # get_files will not find the sld if it doesn't match the base name
    # so we've worked around that in the view - if provided, it will be here
    if upload_session.import_sld_file:
        _log('using provided sld file')
        base_file = upload_session.base_file
        sld_file = os.path.join(
            os.path.dirname(base_file), upload_session.import_sld_file
            )

        f = open(sld_file, 'r')
        sld = f.read()
        f.close()
    else:
        sld = get_sld_for(publishing)

    if sld is not None:
        try:
            cat.create_style(name, sld)
        except geoserver.catalog.ConflictingDataError, e:
            msg = 'There was already a style named %s in GeoServer, cannot overwrite: "%s"' % (name, str(e))
            # what are we doing with this var?
            # style = cat.get_style(name)
            logger.warn(msg)
            e.args = (msg,)

        #FIXME: Should we use the fully qualified typename?
        publishing.default_style = cat.get_style(name)
        _log('default style set to %s', name)
        cat.save(publishing)

    _log('Creating Django record for [%s]', name)
    resource = import_session.tasks[0].items[0].resource
    target = import_session.tasks[0].target
    upload_session.set_target(target)
    typename = "%s:%s" % (target.workspace.name, resource.name)
    layer_uuid = str(uuid.uuid1())

    title = upload_session.layer_title
    abstract = upload_session.layer_abstract

    # @todo hacking - any cached layers might cause problems (maybe
    # delete hook on layer should fix this?)

    cat._cache.clear()

    storeType = 'dataStore' if target.resource_type == 'featureType' else 'coverageStore'

    saved_layer, created = Layer.objects.get_or_create(
        name=resource.name,
        defaults=dict(
            store=target.name,
            storeType=storeType,
            typename=typename,
            workspace=target.workspace.name,
            title=title or resource.title,
            uuid=layer_uuid,
            abstract=abstract or '',
            owner=user,
            )
        )

    # Should we throw a clearer error here?
    assert saved_layer is not None

    # @todo if layer was not created, need to ensure upload target is
    # same as existing target

    _log('layer was created : %s', created)

    if created:
        saved_layer.set_default_permissions()

    # Create the points of contact records for the layer
    # A user without a profile might be uploading this
    _log('Creating points of contact records for [%s]', name)
    poc_contact, __ = Profile.objects.get_or_create(user=user,
                                           defaults={"name": user.username })
    author_contact, __ = Profile.objects.get_or_create(user=user,
                                           defaults={"name": user.username })
    saved_layer.poc = poc_contact
    saved_layer.metadata_author = author_contact

    # look for xml
    xml_file = find_file_re(upload_session.base_file, '.*\.xml')
    if xml_file:
        saved_layer.metadata_uploaded = True
        # get model properties from XML
        vals, keywords = set_metadata(open(xml_file[0]).read())

        # set taggit keywords
        saved_layer.keywords.add(*keywords)

        # set model properties
        for (key, value) in vals.items():
            setattr(saved_layer, key, value)

        saved_layer.save()

    # Set default permissions on the newly created layer
    # FIXME: Do this as part of the post_save hook

    permissions = upload_session.permissions
    _log('Setting default permissions for [%s]', name)
    if permissions is not None:
        layer_set_permissions(saved_layer, permissions)

    _log('Verifying the layer [%s] was created correctly' % name)

    # Verify the object was saved to the Django database
    # @revisit - this should always work since we just created it above and the
    # message is confusing
    try:
        Layer.objects.get(name=name)
    except Layer.DoesNotExist, e:
        msg = ('There was a problem saving the layer %s to Django. Error is: %s' % (name, str(e)))
        logger.exception(msg)
        logger.debug('Attempting to clean up after failed save for layer [%s]', name)
        # Since the layer creation was not successful, we need to clean up
        # @todo implement/test cleanup
        # cleanup(name, layer_uuid)
        raise GeoNodeException(msg)

    # Verify it is correctly linked to GeoServer
    _log('Verifying the layer [%s] was created in GeoServer correctly' % name)
    try:
        saved_layer.verify()
    except GeoNodeException, e:
        msg = ('The layer [%s] was not correctly saved to GeoServer. Error is: %s' % (name, str(e)))
        logger.exception(msg)
        e.args = (msg,)
        # Deleting the layer
        saved_layer.delete()
        raise

    if upload_session.tempdir and os.path.exists(upload_session.tempdir):
        shutil.rmtree(upload_session.tempdir)

    signals.upload_complete.send(sender=final_step, layer=saved_layer)

    upload = Upload.objects.get(import_id = upload_session.import_session.id)
    _log('Reloading Import session for [%s] one last time' % name)
    import_session = import_session.reload()
    upload.import_session = import_session
    upload.layer = saved_layer
    upload.save()
    return saved_layer
