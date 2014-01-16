# -*- coding: utf-8 -*-
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

"""Utilities for managing GeoNode layers
"""

# Standard Modules
import logging
import re
import uuid
import os
import glob
import sys

# Django functionality
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.conf import settings


# Geonode functionality
from geonode import GeoNodeException
from geonode.utils import check_geonode_is_up
from geonode.people.utils import get_valid_user
from geonode.layers.models import Layer, Style
from geonode.people.models import Profile
from geonode.geoserver.helpers import cascading_delete, get_sld_for, delete_from_postgis
from geonode.layers.metadata import set_metadata
from geonode.security.enumerations import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.base.models import SpatialRepresentationType, TopicCategory
from geonode.utils import ogc_server_settings
from geonode.upload.files import _clean_string, _rename_zip
# Geoserver functionality
import geoserver
from geoserver.catalog import FailedRequestError, UploadError
from geoserver.catalog import ConflictingDataError
from geoserver.resource import FeatureType, Coverage
from zipfile import ZipFile

logger = logging.getLogger('geonode.layers.utils')

_separator = '\n' + ('-' * 100) + '\n'


def layer_set_permissions(layer, perm_spec):
    if "authenticated" in perm_spec:
        layer.set_gen_level(AUTHENTICATED_USERS, perm_spec['authenticated'])
    if "anonymous" in perm_spec:
        layer.set_gen_level(ANONYMOUS_USERS, perm_spec['anonymous'])
    if isinstance(perm_spec['users'], dict): perm_spec['users'] = perm_spec['users'].items()
    users = [n[0] for n in perm_spec['users']]
    excluded = users + [layer.owner]
    existing = layer.get_user_levels().exclude(user__username__in=excluded)
    existing.delete()
    for username, level in perm_spec['users']:
        user = User.objects.get(username=username)
        layer.set_user_level(user, level)


def layer_type(filename):
    """Finds out if a filename is a Feature or a Vector
       returns a gsconfig resource_type string
       that can be either 'featureType' or 'coverage'
    """
    base_name, extension = os.path.splitext(filename)

    shp_exts = ['.shp',]
    cov_exts = ['.tif', '.tiff', '.geotiff', '.geotif']
    csv_exts = ['.csv']
    kml_exts = ['.kml']

    if extension.lower() == '.zip':
        zf = ZipFile(filename)
        # ZipFile doesn't support with statement in 2.6, so don't do it
        try:
            for n in zf.namelist():
                b, e = os.path.splitext(n.lower())
                if e in shp_exts or e in cov_exts or e in csv_exts:
                    base_name, extension = b,e
        finally:
            zf.close()

    if extension.lower() in shp_exts + csv_exts + kml_exts:
         return FeatureType.resource_type
    elif extension.lower() in cov_exts:
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

    # shapefile XML metadata is sometimes named base_name.shp.xml
    # try looking for filename.xml if base_name.xml does not exist
    if len(matches) == 0:
        matches = glob.glob(filename + ".[xX][mM][lL]")

    if len(matches) == 1:
        files['xml'] = matches[0]
    elif len(matches) > 1:
        msg = ('Multiple XML files for %s exist; they need to be '
               'distinct by spelling and not just case.') % filename
        raise GeoNodeException(msg)

    return files


def get_valid_name(layer_name):
    """
    Create a brand new name
    """

    name = _clean_string(layer_name)
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

    if 'geonode.catalogue' in settings.INSTALLED_APPS:
        from geonode.catalogue import get_catalogue
        catalogue = get_catalogue()
        catalogue.remove_record(uuid)
        logger.warning('Finished cleanup after failed Catalogue/Django '
                       'import for layer: %s', name)


def save(layer, base_file, user, overwrite=True, title=None,
         abstract=None, permissions=None, keywords=(), charset='UTF-8'):
    """Upload layer data to Geoserver and registers it with Geonode.

       If specified, the layer given is overwritten, otherwise a new layer
       is created.
    """
    logger.info(_separator)

    # Step -1. Verify if the filename is in ascii format.
    try:
        base_file.decode('ascii')
    except UnicodeEncodeError:
        msg = "Please use only characters from the english alphabet for the filename. '%s' is not yet supported." % os.path.basename(base_file).encode('UTF-8')
        raise GeoNodeException(msg)

    logger.info('Uploading layer: [%s], base filename: [%s]', layer, base_file)
    # Step 0. Verify the file exists
    logger.info('>>> Step 0. Verify if the file %s exists so we can create '
                'the layer [%s]' % (base_file, layer))
    if not os.path.exists(base_file):
        msg = ('Could not open %s to save %s. Make sure you are using a '
               'valid file' % (base_file, layer))
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

        # If the store is empty, we just delete it.
        if len(resources) == 0:
            cat.delete(store)
        else:
            # If our resource is already configured in the store it needs
            # to have the right resource type
            for resource in resources:
                if resource.name == name:
                    msg = 'Name already in use and overwrite is False'
                    assert overwrite, msg
                    existing_type = resource.resource_type
                    if existing_type != the_layer_type:
                        msg = ('Type of uploaded file %s (%s) '
                               'does not match type of existing '
                               'resource type '
                               '%s' % (name, the_layer_type, existing_type))
                        logger.info(msg)
                        raise GeoNodeException(msg)

    # Step 3. Identify whether it is vector or raster and which extra files
    # are needed.
    logger.info('>>> Step 3. Identifying if [%s] is vector or raster and '
                'gathering extra files', name)
    if the_layer_type == FeatureType.resource_type:
        logger.debug('Uploading vector layer: [%s]', base_file)
        if ogc_server_settings.DATASTORE:
            create_store_and_resource = _create_db_featurestore
        else:
            create_store_and_resource = _create_featurestore
    elif the_layer_type == Coverage.resource_type:
        logger.debug("Uploading raster layer: [%s]", base_file)
        create_store_and_resource = _create_coveragestore
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
        if files['base'][-4:] == ".zip":
            _rename_zip(files['base'], name)
        main_file = files['base']
        data = main_file
    # ------------------

    try:
        store, gs_resource = create_store_and_resource(name,
                                                       data,
                                                       charset=charset,
                                                       overwrite=overwrite)
    except UploadError, e:
        msg = ('Could not save the layer %s, there was an upload '
               'error: %s' % (name, str(e)))
        logger.warn(msg)
        e.args = (msg,)
        raise
    except ConflictingDataError, e:
        # A datastore of this name already exists
        msg = ('GeoServer reported a conflict creating a store with name %s: '
               '"%s". This should never happen because a brand new name '
               'should have been generated. But since it happened, '
               'try renaming the file or deleting the store in '
               'GeoServer.' % (name, str(e)))
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
        msg = ('GeoNode encountered problems when creating layer %s.'
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
           -90 <= miny <= 90 and -90 <= maxy <= 90:
            logger.info('GeoServer failed to detect the projection for layer '
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
            logger.info(msg, name)
            cascading_delete(cat, name)
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

    workspace = gs_resource.store.workspace.name
    saved_layer, created = Layer.objects.get_or_create(name=gs_resource.name,
                                                       workspace=workspace,
                                                       defaults=defaults)

    saved_layer.keywords.add(*keywords)

    logger.info('>>> Step XML. Processing XML metadata (if available)')
    # Step XML. If an XML metadata document is uploaded,
    # parse the XML metadata and update uuid and URLs as per the content model

    if 'xml' in files:
        saved_layer.metadata_uploaded = True
        # get model properties from XML
        vals, keywords = set_metadata(open(files['xml']).read())

        # set taggit keywords
        saved_layer.keywords.add(*keywords)

        # set model properties
        for (key, value) in vals.items():
            if key == 'spatial_representation_type':
                value = SpatialRepresentationType(identifier=value)
            elif key == 'topic_category':
                category, created = TopicCategory.objects.get_or_create(identifier=value.lower(), gn_description=value)

                saved_layer.category = category
            else:
                setattr(saved_layer, key, value)

        saved_layer.save()

    # Step 11. Set default permissions on the newly created layer
    # FIXME: Do this as part of the post_save hook
    logger.info('>>> Step 10. Setting default permissions for [%s]', name)

    if permissions is not None and len(permissions.keys()) > 0:
        layer_set_permissions(saved_layer, permissions)
    else:
        saved_layer.set_default_permissions()

    # Step 12. Verify the layer was saved correctly and clean up if needed
    logger.info('>>> Step 11. Verifying the layer [%s] was created '
                'correctly' % name)

    # Verify the object was saved to the Django database
    try:
        Layer.objects.get(typename=typename)
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


def get_default_user():
    """Create a default user
    """
    superusers = User.objects.filter(is_superuser=True).order_by('id')
    if superusers.count() > 0:
        # Return the first created superuser
        return superusers[0]
    else:
        raise GeoNodeException('You must have an admin account configured '
                               'before importing data. '
                               'Try: django-admin.py createsuperuser')

def file_upload(filename, user=None, title=None,
                skip=True, overwrite=False, keywords=()):
    """Saves a layer in GeoNode asking as little information as possible.
       Only filename is required, user and title are optional.
    """
    # Do not do attempt to do anything unless geonode is running
    check_geonode_is_up()

    # Get a valid user
    theuser = get_valid_user(user)

    # Set a default title that looks nice ...
    if title is None:
        basename = os.path.splitext(os.path.basename(filename))[0]
        title = basename.title().replace('_', ' ')

    # ... and use a url friendly version of that title for the name
    name = slugify(title).replace('-', '_')

    # Note that this will replace any existing layer that has the same name
    # with the data that is being passed.
    try:
        layer = Layer.objects.get(name=name)
    except Layer.DoesNotExist:
        layer = name

    new_layer = save(layer, filename, theuser, overwrite,
                     keywords=keywords, title=title)

    return new_layer


def upload(incoming, user=None, overwrite=False,
           keywords=(), skip=True, ignore_errors=True,
           verbosity=1, console=None):
    """Upload a directory of spatial data files to GeoNode

       This function also verifies that each layer is in GeoServer.

       Supported extensions are: .shp, .tif, and .zip (of a shapefile).
       It catches GeoNodeExceptions and gives a report per file
    """
    if verbosity > 1:
        print >> console, "Verifying that GeoNode is running ..."
    check_geonode_is_up()

    if console is None:
        console = open(os.devnull, 'w')

    potential_files = []
    if os.path.isfile(incoming):
        ___, short_filename = os.path.split(incoming)
        basename, extension = os.path.splitext(short_filename)
        filename = incoming

        if extension in ['.tif', '.shp', '.zip']:
            potential_files.append((basename, filename))

    elif not os.path.isdir(incoming):
        msg = ('Please pass a filename or a directory name as the "incoming" '
               'parameter, instead of %s: %s' % (incoming, type(incoming)))
        logger.exception(msg)
        raise GeoNodeException(msg)
    else:
        datadir = incoming
        for root, dirs, files in os.walk(datadir):
            for short_filename in files:
                basename, extension = os.path.splitext(short_filename)
                filename = os.path.join(root, short_filename)
                if extension in ['.tif', '.shp', '.zip']:
                    potential_files.append((basename, filename))

    # After gathering the list of potential files,
    # let's process them one by one.
    number = len(potential_files)
    if verbosity > 1:
        msg = "Found %d potential layers." % number
        print >> console, msg

    output = []
    for i, file_pair in enumerate(potential_files):
        basename, filename = file_pair

        existing_layers = Layer.objects.filter(name=basename)

        if existing_layers.count() > 0:
            existed = True
        else:
            existed = False

        if existed and skip:
            save_it = False
            status = 'skipped'
            layer = existing_layers[0]
            if verbosity > 0:
                msg = ('Stopping process because '
                       '--overwrite was not set '
                       'and a layer with this name already exists.')
                print >> sys.stderr, msg
        else:
            save_it = True

        if save_it:
            try:
                layer = file_upload(filename,
                                    user=user,
                                    overwrite=overwrite,
                                    keywords=keywords,
                                    )
                if not existed:
                    status = 'created'
                else:
                    status = 'updated'
            except Exception, e:
                if ignore_errors:
                    status = 'failed'
                    exception_type, error, traceback = sys.exc_info()
                else:
                    if verbosity > 0:
                        msg = ('Stopping process because '
                               '--ignore-errors was not set '
                               'and an error was found.')
                        print >> sys.stderr, msg
                        msg = 'Failed to process %s' % filename
                        raise Exception(msg, e), None, sys.exc_info()[2]

        msg = "[%s] Layer for '%s' (%d/%d)" % (status, filename, i + 1, number)
        info = {'file': filename, 'status': status}
        if status == 'failed':
            info['traceback'] = traceback
            info['exception_type'] = exception_type
            info['error'] = error
        else:
            info['name'] = layer.name

        output.append(info)
        if verbosity > 0:
            print >> console, msg
    return output


def _create_featurestore(name, data, overwrite=False, charset="UTF-8"):
    cat = Layer.objects.gs_catalog
    cat.create_featurestore(name, data, overwrite=overwrite, charset=charset)
    return cat.get_store(name), cat.get_resource(name)


def _create_coveragestore(name, data, overwrite=False, charset="UTF-8"):
    cat = Layer.objects.gs_catalog
    cat.create_coveragestore(name, data, overwrite=overwrite)
    return cat.get_store(name), cat.get_resource(name)


def _create_db_featurestore(name, data, overwrite=False, charset="UTF-8"):
    """Create a database store then use it to import a shapefile.

    If the import into the database fails then delete the store
    (and delete the PostGIS table for it).
    """
    cat = Layer.objects.gs_catalog
    dsname = ogc_server_settings.DATASTORE

    try:
        ds = cat.get_store(dsname)
    except FailedRequestError:
        ds = cat.create_datastore(dsname)
        db = ogc_server_settings.datastore_db
        db_engine = 'postgis' if \
            'postgis' in db['ENGINE'] else db['ENGINE']
        ds.connection_parameters.update(
            host = db['HOST'],
            port = db['PORT'],
            database = db['NAME'],
            user = db['USER'],
            passwd = db['PASSWORD'],
            dbtype = db_engine
            )
        cat.save(ds)
        ds = cat.get_store(dsname)

    try:
        cat.add_data_to_store(ds, name, data,
                              overwrite=overwrite,
                              charset=charset)
        return ds, cat.get_resource(name, store=ds)
    except Exception:
        # FIXME(Ariel): This is not a good idea, today there was a problem 
        # accessing postgis that caused add_data_to_store to fail,
        # for the same reasons the call to delete_from_postgis below failed too
        # I am commenting it out and filing it as issue #1058
        #delete_from_postgis(name)
        raise

def style_update(request, url):
    """
    Sync style stuff from GS to GN.
    Ideally we should call this from a view straight from GXP, and we should use
    gsConfig, that at this time does not support styles updates. Before gsConfig
    is updated, for now we need to parse xml.
    In case of a DELETE, we need to query request.path to get the style name,
    and then remove it.
    In case of a POST or PUT, we need to parse the xml from
    request.raw_post_data, which is in this format:
    """
    if request.method in ('POST', 'PUT'): # we need to parse xml
        import xml.etree.ElementTree as ET
        tree = ET.ElementTree(ET.fromstring(request.raw_post_data))
        elm_namedlayer_name=tree.findall('.//{http://www.opengis.net/sld}Name')[0]
        elm_user_style_name=tree.findall('.//{http://www.opengis.net/sld}Name')[1]
        elm_user_style_title=tree.find('.//{http://www.opengis.net/sld}Title')
        if not elm_user_style_title:
            elm_user_style_title = elm_user_style_name
        layer_name=elm_namedlayer_name.text
        style_name=elm_user_style_name.text
        sld_body='<?xml version="1.0" encoding="UTF-8"?>%s' % request.raw_post_data
        if request.method == 'POST': # add style in GN and associate it to layer
            style = Style(name=style_name, sld_body=sld_body, sld_url=url)
            style.save()
            layer = Layer.objects.all().filter(typename=layer_name)[0]
            style.layer_styles.add(layer)
            style.save()
        if request.method == 'PUT': # update style in GN
            style = Style.objects.all().filter(name=style_name)[0]
            style.sld_body=sld_body
            style.sld_url=url
            if len(elm_user_style_title.text)>0:
                style.sld_title = elm_user_style_title.text
            style.save()
            for layer in style.layer_styles.all():
                layer.update_thumbnail()
    if request.method == 'DELETE': # delete style from GN
        style_name = os.path.basename(request.path)
        style = Style.objects.all().filter(name=style_name)[0]
        style.delete()

