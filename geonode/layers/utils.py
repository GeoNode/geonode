# -*- coding: utf-8 -*-
"""Utilities for managing GeoNode layers
"""

# Standard Modules
import logging
import re
import uuid
import os
import datetime
import traceback
import inspect
import string
import urllib2
from lxml import etree
import glob

# Django functionality
from django.template.defaultfilters import slugify
from django.conf import settings


# Geonode functionality
from geonode import GeoNodeException
from geonode.utils import check_geonode_is_up
from geonode.catalogue import get_catalogue
from geonode.people.utils import get_valid_user
from geonode.layers.models import Layer
from geonode.people.models import Contact
from geonode.gs_helpers import cascading_delete, get_sld_for, delete_from_postgis
from django.contrib.auth.models import User
from geonode.security.models import AUTHENTICATED_USERS, ANONYMOUS_USERS
# Geoserver functionality
import geoserver
from geoserver.catalog import FailedRequestError
from geoserver.resource import FeatureType, Coverage

logger = logging.getLogger('geonode.layers.utils')

_separator = '\n' + ('-' * 100) + '\n'


def layer_set_permissions(layer, perm_spec):
    if "authenticated" in perm_spec:
        layer.set_gen_level(AUTHENTICATED_USERS, perm_spec['authenticated'])
    if "anonymous" in perm_spec:
        layer.set_gen_level(ANONYMOUS_USERS, perm_spec['anonymous'])
    users = [n[0] for n in perm_spec['users']]
    layer.get_user_levels().exclude(user__username__in = users + [layer.owner]).delete()
    for username, level in perm_spec['users']:
        user = User.objects.get(username=username)
        layer.set_user_level(user, level)



def layer_type(filename):
    """Finds out if a filename is a Feature or a Vector
       returns a gsconfig resource_type string
       that can be either 'featureType' or 'coverage'
    """
    extension = os.path.splitext(filename)[1]
    if extension.lower() in ['.shp']:
        return FeatureType.resource_type
    elif extension.lower() in ['.tif', '.tiff', '.geotiff', '.geotif']:
        return Coverage.resource_type
    else:
        msg = ('Saving of extension [%s] is not implemented' % extension)
        raise GeoNodeException(msg)


def get_files(filename):
    """Converts the data to Shapefiles or Geotiffs and returns
       a dictionary with all the required files
    """
    files = {'base': filename}

    base_name, extension = os.path.splitext(filename)
    #Replace special characters in filenames - []{}()
    glob_name = re.sub(r'([\[\]\(\)\{\}])', r'[\g<1>]', base_name)

    if extension.lower() == '.shp':
        required_extensions = dict(
            shp='.[sS][hH][pP]', dbf='.[dD][bB][fF]', shx='.[sS][hH][xX]')
        for ext, pattern in required_extensions.iteritems():
            matches = glob.glob(glob_name + pattern)
            if len(matches) == 0:
                msg = ('Expected helper file %s does not exist; a Shapefile '
                       'requires helper files with the following extensions: '
                       '%s') % (base_name + "." + ext,
                                required_extensions.keys())
                raise GeoNodeException(msg)
            elif len(matches) > 1:
                msg = ('Multiple helper files for %s exist; they need to be '
                       'distinct by spelling and not just case.') % filename
                raise GeoNodeException(msg)
            else:
                files[ext] = matches[0]

        matches = glob.glob(glob_name + ".[pP][rR][jJ]")
        if len(matches) == 1:
            files['prj'] = matches[0]
        elif len(matches) > 1:
            msg = ('Multiple helper files for %s exist; they need to be '
                   'distinct by spelling and not just case.') % filename
            raise GeoNodeException(msg)

    matches = glob.glob(glob_name + ".[sS][lL][dD]")
    if len(matches) == 1:
        files['sld'] = matches[0]
    elif len(matches) > 1:
        msg = ('Multiple style files for %s exist; they need to be '
               'distinct by spelling and not just case.') % filename
        raise GeoNodeException(msg)

    matches = glob.glob(base_name + ".[xX][mM][lL]")

    if len(matches) == 1:
        files['xml'] = matches[0]
    elif len(matches) > 1:
        msg = ('Multiple XML files for %s exist; they need to be '
               'distinct by spelling and not just case.') % filename
        raise GeoNodeException(msg)

    return files


def get_valid_name(layer_name):
    """Create a brand new name
    """
    xml_unsafe = re.compile(r"(^[^a-zA-Z\._]+)|([^a-zA-Z\._0-9]+)")
    name = xml_unsafe.sub("_", layer_name)
    proposed_name = name
    count = 1
    while Layer.objects.filter(name=proposed_name).count() > 0:
        proposed_name = "%s_%d" % (name, count)
        count = count + 1
        logger.info('Requested name already used; adjusting name '
                    '[%s] => [%s]', layer_name, proposed_name)
    else:
        logger.info("Using name as requested")

    return proposed_name


## TODO: Remove default arguments here, they are never used.
def get_valid_layer_name(layer=None, overwrite=False):
    """Checks if the layer is a string and fetches it from the database.
    """
    # The first thing we do is get the layer name string
    if isinstance(layer, Layer):
        layer_name = layer.name
    elif isinstance(layer, basestring):
        layer_name = layer
    else:
        msg = ('You must pass either a filename or a GeoNode layer object')
        raise GeoNodeException(msg)

    if overwrite:
        #FIXME: What happens if there is a store in GeoServer with that name
        # that is not registered in GeoNode?
        return layer_name
    else:
        return get_valid_name(layer_name)

def cleanup(name, uuid):
   """Deletes GeoServer and Catalogue records for a given name.

      Useful to clean the mess when something goes terribly wrong.
      It also verifies if the Django record existed, in which case
      it performs no action.
   """
   try:
       Layer.objects.get(name=name)
   except Layer.DoesNotExist, e:
       pass
   else:
       msg = ('Not doing any cleanup because the layer %s exists in the '
              'Django db.' % name)
       raise GeoNodeException(msg)

   cat = Layer.objects.gs_catalog
   gs_store = None
   gs_layer = None
   gs_resource = None
   # FIXME: Could this lead to someone deleting for example a postgis db
   # with the same name of the uploaded file?.
   try:
       gs_store = cat.get_store(name)
       if gs_store is not None:
           gs_layer = cat.get_layer(name)
           if gs_layer is not None:
               gs_resource = gs_layer.resource
       else:
           gs_layer = None
           gs_resource = None
   except FailedRequestError, e:
       msg = ('Couldn\'t connect to GeoServer while cleaning up layer '
              '[%s] !!', str(e))
       logger.warning(msg)

   if gs_layer is not None:
       try:
           cat.delete(gs_layer)
       except:
           logger.warning("Couldn't delete GeoServer layer during cleanup()")
   if gs_resource is not None:
       try:
           cat.delete(gs_resource)
       except:
           msg = 'Couldn\'t delete GeoServer resource during cleanup()'
           logger.warning(msg)
   if gs_store is not None:
       try:
           cat.delete(gs_store)
       except:
           logger.warning("Couldn't delete GeoServer store during cleanup()")

   logger.warning('Deleting dangling Catalogue record for [%s] '
                  '(no Django record to match)', name)

   catalogue = get_catalogue()
   catalogue.remove_record(uuid)
   logger.warning('Finished cleanup after failed Catalogue/Django '
                  'import for layer: %s', name)

def save(layer, base_file, user, overwrite = True, title=None,
         abstract=None, permissions=None, keywords = ()):
    """Upload layer data to Geoserver and registers it with Geonode.

       If specified, the layer given is overwritten, otherwise a new layer
       is created.
    """
    logger.info(_separator)
    logger.info('Uploading layer: [%s], base filename: [%s]', layer, base_file)

    # Step 0. Verify the file exists
    logger.info('>>> Step 0. Verify if the file %s exists so we can create '
                'the layer [%s]' % (base_file, layer))
    if not os.path.exists(base_file):
        msg = ('Could not open %s to save %s. Make sure you are using a '
               'valid file' %(base_file, layer))
        logger.warn(msg)
        raise GeoNodeException(msg)

    # Step 1. Figure out a name for the new layer, the one passed might not
    # be valid or being used.
    logger.info('>>> Step 1. Figure out a name for %s', layer)
    name = get_valid_layer_name(layer, overwrite)

    # Step 2. Check that it is uploading to the same resource type as
    # the existing resource
    logger.info('>>> Step 2. Make sure we are not trying to overwrite a '
                'existing resource named [%s] with the wrong type', name)
    the_layer_type = layer_type(base_file)

    # Get a short handle to the gsconfig geoserver catalog
    cat = Layer.objects.gs_catalog

    # Check if the store exists in geoserver
    try:
        store = cat.get_store(name)
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
                msg = ('The layer exists and the overwrite parameter is '
                       '%s' % overwrite)
                raise GeoNodeException(msg)
        else:
            # If our resource is already configured in the store it needs
            # to have the right resource type
            for resource in resources:
                if resource.name == name:
                    msg = 'Name already in use and overwrite is False'
                    assert overwrite, msg
                    existing_type = resource.resource_type
                    if existing_type != the_layer_type:
                        msg =  ('Type of uploaded file %s (%s) does not match '
                                'type of existing resource type '
                                '%s' % (name,
                                        the_layer_type,
                                        existing_type))
                        logger.info(msg)
                        raise GeoNodeException(msg)

    # Step 3. Identify whether it is vector or raster and which extra files
    # are needed.
    logger.info('>>> Step 3. Identifying if [%s] is vector or raster and '
                'gathering extra files', name)
    if the_layer_type == FeatureType.resource_type:
        logger.debug('Uploading vector layer: [%s]', base_file)
        if settings.DB_DATASTORE:
            create_store_and_resource = _create_db_featurestore
        else:
            def create_store_and_resource(name, data, overwrite):
                cat.create_featurestore(name, data, overwrite=overwrite)
                return cat.get_store(name), cat.get_resource(name)
    elif the_layer_type == Coverage.resource_type:
        logger.debug("Uploading raster layer: [%s]", base_file)
        def create_store_and_resource(name, data, overwrite):
            cat.create_coveragestore(name, data, overwrite=overwrite)
            return cat.get_store(name), cat.get_resource(name)
    else:
        msg = ('The layer type for name %s is %s. It should be '
               '%s or %s,' % (name,
                              the_layer_type,
                              FeatureType.resource_type,
                              Coverage.resource_type))
        logger.warn(msg)
        raise GeoNodeException(msg)

    # Step 4. Create the store in GeoServer
    logger.info('>>> Step 4. Starting upload of [%s] to GeoServer...', name)

    # Get the helper files if they exist
    files = get_files(base_file)

    data = files

    #FIXME: DONT DO THIS
    #-------------------
    if 'shp' not in files:
        main_file = files['base']
        data = main_file
    # ------------------

    try:
        store, gs_resource = create_store_and_resource(name, data, overwrite=overwrite)
    except geoserver.catalog.UploadError, e:
        msg = ('Could not save the layer %s, there was an upload '
               'error: %s' % (name, str(e)))
        logger.warn(msg)
        e.args = (msg,)
        raise
    except geoserver.catalog.ConflictingDataError, e:
        # A datastore of this name already exists
        msg = ('GeoServer reported a conflict creating a store with name %s: '
               '"%s". This should never happen because a brand new name '
               'should have been generated. But since it happened, '
               'try renaming the file or deleting the store in '
               'GeoServer.'  % (name, str(e)))
        logger.warn(msg)
        e.args = (msg,)
        raise
    else:
        logger.debug('Finished upload of [%s] to GeoServer without '
                     'errors.', name)


    # Step 5. Create the resource in GeoServer
    logger.info('>>> Step 5. Generating the metadata for [%s] after '
                'successful import to GeoSever', name)

    # Verify the resource was created
    if gs_resource is not None:
        assert gs_resource.name == name
    else:
        msg = ('GeoNode encounterd problems when creating layer %s.'
               'It cannot find the Layer that matches this Workspace.'
               'try renaming your files.' % name)
        logger.warn(msg)
        raise GeoNodeException(msg)

    # Step 6. Make sure our data always has a valid projection
    # FIXME: Put this in gsconfig.py
    logger.info('>>> Step 6. Making sure [%s] has a valid projection' % name)
    if gs_resource.latlon_bbox is None:
        box = gs_resource.native_bbox[:4]
        minx, maxx, miny, maxy = [float(a) for a in box]
        if -180 <= minx <= 180 and -180 <= maxx <= 180 and \
           -90  <= miny <= 90  and -90  <= maxy <= 90:
            logger.warn('GeoServer failed to detect the projection for layer '
                        '[%s]. Guessing EPSG:4326', name)
            # If GeoServer couldn't figure out the projection, we just
            # assume it's lat/lon to avoid a bad GeoServer configuration

            gs_resource.latlon_bbox = gs_resource.native_bbox
            gs_resource.projection = "EPSG:4326"
            cat.save(gs_resource)
        else:
            msg = ('GeoServer failed to detect the projection for layer '
                   '[%s]. It doesn\'t look like EPSG:4326, so backing out '
                   'the layer.')
            logger.warn(msg, name)
            cascading_delete(cat, gs_resource)
            raise GeoNodeException(msg % name)

    # Step 7. Create the style and assign it to the created resource
    # FIXME: Put this in gsconfig.py
    logger.info('>>> Step 7. Creating style for [%s]' % name)
    publishing = cat.get_layer(name)

    if 'sld' in files:
        f = open(files['sld'], 'r')
        sld = f.read()
        f.close()
    else:
        sld = get_sld_for(publishing)

    if sld is not None:
        try:
            cat.create_style(name, sld)
        except geoserver.catalog.ConflictingDataError, e:
            msg = ('There was already a style named %s in GeoServer, '
                   'cannot overwrite: "%s"' % (name, str(e)))
            logger.warn(msg)
            e.args = (msg,)

        #FIXME: Should we use the fully qualified typename?
        publishing.default_style = cat.get_style(name)
        cat.save(publishing)

    # Step 10. Create the Django record for the layer
    logger.info('>>> Step 10. Creating Django record for [%s]', name)
    # FIXME: Do this inside the layer object
    typename = gs_resource.store.workspace.name + ':' + gs_resource.name
    layer_uuid = str(uuid.uuid1())
    defaults = dict(store=gs_resource.store.name,
                    storeType=gs_resource.store.resource_type,
                    typename=typename,
                    title=title or gs_resource.title,
                    uuid=layer_uuid,
                    abstract=abstract or gs_resource.abstract or '',
                    owner=user)
    saved_layer, created = Layer.objects.get_or_create(name=gs_resource.name,
                                                       workspace=gs_resource.store.workspace.name,
                                                       defaults=defaults)

    
    saved_layer.keywords.add(*keywords)

    # Step 9. Create the points of contact records for the layer
    # A user without a profile might be uploading this
    logger.info('>>> Step 9. Creating points of contact records for '
                '[%s]', name)
    poc_contact, __ = Contact.objects.get_or_create(user=user,
                                           defaults={"name": user.username })
    author_contact, __ = Contact.objects.get_or_create(user=user,
                                           defaults={"name": user.username })

    logger.debug('Creating poc and author records for %s', poc_contact)

    saved_layer.poc = poc_contact
    saved_layer.metadata_author = author_contact

    # Step 11. Set default permissions on the newly created layer
    # FIXME: Do this as part of the post_save hook
    logger.info('>>> Step 11. Setting default permissions for [%s]', name)
    if permissions is not None:

        layer_set_permissions(saved_layer, permissions)
    else:
        saved_layer.set_default_permissions()

    # Step 12. Verify the layer was saved correctly and clean up if needed
    logger.info('>>> Step 12. Verifying the layer [%s] was created '
                'correctly' % name)

    # Verify the object was saved to the Django database
    try:
        Layer.objects.get(name=name)
    except Layer.DoesNotExist, e:
        msg = ('There was a problem saving the layer %s to Catalogue/Django. '
               'Error is: %s' % (layer, str(e)))
        logger.exception(msg)
        logger.debug('Attempting to clean up after failed save for layer '
                     '[%s]', name)
        # Since the layer creation was not successful, we need to clean up
        cleanup(name, layer_uuid)
        raise GeoNodeException(msg)

    # Verify it is correctly linked to GeoServer and the catalogue
    try:
        # FIXME: Implement a verify method that makes sure it was
        # saved in both Catalogue and GeoServer
        saved_layer.verify()
    except NotImplementedError, e:
        logger.exception('>>> FIXME: Please, if you can write python code, '
                         'implement "verify()" '
                         'method in geonode.maps.models.Layer')
    except GeoNodeException, e:
        msg = ('The layer [%s] was not correctly saved to '
               'Catalogue/GeoServer. Error is: %s' % (layer, str(e)))
        logger.exception(msg)
        e.args = (msg,)
        # Deleting the layer
        saved_layer.delete()
        raise

    # Return the created layer object
    return saved_layer


def file_upload(filename, user=None, title=None, overwrite=True, keywords=()):
    """Saves a layer in GeoNode asking as little information as possible.
       Only filename is required, user and title are optional.
    """
    # Do not do attemt to do anything unless geonode is running
    check_geonode_is_up()

    # Get a valid user
    theuser = get_valid_user(user)

    # Set a default title that looks nice ...
    if title is None:
        basename = os.path.splitext(os.path.basename(filename))[0]
        title = basename.title().replace('_', ' ')

    # ... and use a url friendly version of that title for the name
    name = slugify(title).replace('-','_')

    # Note that this will replace any existing layer that has the same name
    # with the data that is being passed.
    try:
        layer = Layer.objects.get(name=name)
    except Layer.DoesNotExist:
        layer = name

    new_layer = save(layer, filename, theuser, overwrite, keywords=keywords)

    return new_layer


def upload(incoming, user=None, overwrite=True, keywords = ()):
    """Upload a directory of spatial data files to GeoNode

       This function also verifies that each layer is in GeoServer.

       Supported extensions are: .shp, .tif, and .zip (of a shapfile).
       It catches GeoNodeExceptions and gives a report per file
       >>> batch_upload('/tmp/mydata')
           [{'file': 'data1.tiff', 'name': 'geonode:data1' },
           {'file': 'data2.shp', 'errors': 'Shapefile requires .prj file'}]
    """
    check_geonode_is_up()

    if os.path.isfile(incoming):
        layer = file_upload(incoming,
                            user=user,
                            overwrite=overwrite,
                            keywords = keywords)
        return [{'file': incoming, 'name': layer.name}]
    elif not os.path.isdir(incoming):
        msg = ('Please pass a filename or a directory name as the "incoming" '
               'parameter, instead of %s: %s' % (incoming, type(incoming)))
        logger.exception(msg)
        raise GeoNodeException(msg)
    else:
        datadir = incoming
        results = []

        for root, dirs, files in os.walk(datadir):
            for short_filename in files:
                basename, extension = os.path.splitext(short_filename)
                filename = os.path.join(root, short_filename)
                if extension in ['.tif', '.shp', '.zip']:
                    try:
                        layer = file_upload(filename,
                                            user=user,
                                            title=basename,
                                            overwrite=overwrite,
                                            keywords=keywords
                                           )

                    except GeoNodeException, e:
                        msg = ('[%s] could not be uploaded. Error was: '
                               '%s' % (filename, str(e)))
                        logger.info(msg)
                        results.append({'file': filename, 'errors': msg})
                    else:
                        results.append({'file': filename, 'name': layer.name})
        return results

def _create_db_featurestore(name, data, overwrite = False, charset = None):
    """Create a database store then use it to import a shapefile.

    If the import into the database fails then delete the store
    (and delete the PostGIS table for it).
    """
    cat = Layer.objects.gs_catalog
    try:
        ds = cat.get_store(settings.DB_DATASTORE_NAME)
    except FailedRequestError:
        ds = cat.create_datastore(settings.DB_DATASTORE_NAME)
        ds.connection_parameters.update(
            host=settings.DB_DATASTORE_HOST,
            port=settings.DB_DATASTORE_PORT,
            database=settings.DB_DATASTORE_DATABASE,
            user=settings.DB_DATASTORE_USER,
            passwd=settings.DB_DATASTORE_PASSWORD,
            dbtype=settings.DB_DATASTORE_TYPE)
        cat.save(ds)
        ds = cat.get_store(settings.DB_DATASTORE_NAME)

    try:
        cat.add_data_to_store(ds, name, data, overwrite=overwrite, charset=charset)
        return ds, cat.get_resource(name, store=ds)
    except Exception:
        delete_from_postgis(name)
        raise
