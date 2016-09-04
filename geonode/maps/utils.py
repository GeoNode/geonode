"""GeoNode SDK for managing GeoNode layers and users
"""

# Standard Modules
import logging
from zipfile import ZipFile
from random import choice
import re
from django.db import transaction
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from geonode.maps.models import Map, Layer, MapLayer, Contact, ContactRole, Role, get_csw
from geonode.maps.gs_helpers import fixup_style, cascading_delete, get_sld_for, delete_from_postgis, get_postgis_bbox
import uuid
import os
import glob
import sys
import datetime

# Django functionality
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.conf import settings
from xml.etree.ElementTree import XML, ParseError
from django.utils.translation import ugettext as _

# Geonode functionality
from geonode.maps.models import Contact, Layer, LayerAttribute
from geonode.maps.gs_helpers import cascading_delete, get_sld_for, delete_from_postgis

# Geoserver functionality
import geoserver
from geoserver.catalog import FailedRequestError
from geoserver.resource import FeatureType, Coverage


logger = logging.getLogger("geonode.maps.utils")
_separator = '\n' + ('-' * 100) + '\n'
import math


class GeoNodeException(Exception):
    """Base class for exceptions in this module."""
    pass


def layer_type(filename):
    """Finds out if a filename is a Feature or a Vector
       returns a gsconfig resource_type string
       that can be either 'featureType' or 'coverage'
    """
    extension = os.path.splitext(filename)[1]
    if extension.lower() in ['.shp','.zip']:
        return FeatureType.resource_type
    elif extension.lower() in ['.tif', '.tiff', '.geotiff', '.geotif']:
        return Coverage.resource_type
    else:
        msg = (_('Saving is not implemented for extension ') + extension)
        raise GeoNodeException(msg)

def get_files(filename, sldfile):
    """Converts the data to Shapefiles or Geotiffs and returns
       a dictionary with all the required files
    """
    files = {'base': filename}

    base_name, extension = os.path.splitext(filename)
    #Replace special characters in filenames - []{}()
    glob_name = re.sub(r'([\[\]\(\)\{\}])', r'[\g<1>]', base_name)

    required_extensions = dict(
        shp='.[sS][hH][pP]', dbf='.[dD][bB][fF]', shx='.[sS][hH][xX]', prj='.[pP][rR][jJ]')
    if extension.lower() == '.shp':
        for ext, pattern in required_extensions.iteritems():
            matches = glob.glob(glob_name + pattern)
            if len(matches) == 0:
                msg = ((_('Expected helper file does not exist: ') + base_name + "." + ext +
                _('; a Shapefile requires helper files with the following extensions: ')
                + '%s')) % (required_extensions.keys())
                raise GeoNodeException(msg)
            elif len(matches) > 1:
                msg = ('Multiple helper files for %s exist; they need to be '
                       'distinct by spelling and not just case.') % filename
                raise GeoNodeException(msg)
            else:
                files[ext] = matches[0]
    elif extension.lower() == '.zip':
        zipFiles = ZipFile(filename).namelist()

        for file in zipFiles:
            shapefile, extension = os.path.splitext(file)
            if extension.lower() == '.shp':
                base_name = shapefile
                break

        zipString = ' '.join(zipFiles)
        logger.debug('zipString:%s', zipString)

        for ext, pattern in required_extensions.iteritems():
            logger.debug('basename + pattern:%s', base_name+pattern)
            if re.search(re.escape(base_name) + pattern, zipString) is None:
                msg = ((_('Expected helper file does not exist: ') + base_name + "." + ext +
                _('; a Shapefile requires helper files with the following extensions: ')
                + '%s')) % (required_extensions.keys())
                raise GeoNodeException(msg)

        files['zip'] = filename

    # Always upload stylefile if it exist
    if sldfile and os.path.exists(sldfile):
        files['sld'] = sldfile

    return files


def get_valid_name(layer_name):
    """Create a brand new name
    """
    xml_unsafe = re.compile(r"(^[^a-zA-Z\._]+)|([^a-zA-Z\._0-9]+)")
    name = xml_unsafe.sub("_", layer_name)
    proposed_name = name + "_"  + "".join([choice('qwertyuiopasdfghjklzxcvbnm0123456789') for i in range(3)])
    count = 1
    while Layer.objects.filter(name=proposed_name).count() > 0:
        proposed_name = name + "_"  + "".join([choice('qwertyuiopasdfghjklzxcvbnm0123456789') for i in range(3)])
        logger.info('Requested name already used; adjusting name '
                    '[%s] => [%s]', layer_name, proposed_name)
    else:
        logger.info("Using name as requested")

    return proposed_name.lower()


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
        msg = (_('You must pass either a filename or a GeoNode layer object'))
        raise GeoNodeException(msg)

    # Trim the layer name's length to 40 chars.
    # Workaround for issue #354.
    # https://github.com/GeoNode/geonode/issues/354
    if len(layer_name)>40:
    	layer_name = layer_name[:40]

    if overwrite:
        #FIXME: What happens if there is a store in GeoServer with that name
        # that is not registered in GeoNode?
        return layer_name
    else:
        return get_valid_name(layer_name)


def cleanup(name, layer_id):
    """Deletes GeoServer and GeoNetwork records for a given name.

       Useful to clean the mess when something goes terribly wrong.
       It also verifies if the Django record existed, in which case
       it performs no action.
    """
    try:
        Layer.objects.get(name=name)
    except Layer.DoesNotExist, e:
        pass
    else:
        msg = (('%s ' + _('exists in the Django db, so not doing any cleanup.')) % name)
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
        msg = ((_('Couldn\'t connect to GeoServer while cleaning up layer ') +
               '[%s] !!'), str(e))
        logger.error(msg)

    if gs_layer is not None:
        try:
            cat.delete(gs_layer)
        except Exception:
            logger.exception(_("Couldn't delete GeoServer layer during cleanup()"))
    if gs_resource is not None:
        try:
            cat.delete(gs_resource)
        except Exception:
            msg = _('Couldn\'t delete GeoServer resource during cleanup()')
            logger.exception(msg)
    if gs_store is not None:
        try:
            cat.delete(gs_store)
        except Exception:
            logger.exception(_("Couldn't delete GeoServer store during cleanup()"))

    gn = Layer.objects.geonetwork
    csw_record = gn.get_by_uuid(layer_id)
    if csw_record is not None:
        logger.warning((_('Deleting dangling GeoNetwork record (no Django record to match) for ')
                       +'[%s] '), name)
        try:
            # this is a bit hacky, delete_layer expects an instance of the layer
            # model but it just passes it to a Django template so a dict works
            # too.
            gn.delete_layer({ "uuid": layer_id })
        except Exception:
            logger.exception('Couldn\'t delete GeoNetwork record '
                             'during cleanup()')

    logger.warning('Finished cleanup after failed GeoNetwork/Django '
                   'import for layer: %s', name)


def get_db_store_name(user=None):
    # DB_DATASTORE_NAME is not used anymore now until this is fixed:
    # https://osgeo-org.atlassian.net/browse/GEOS-7533
    # db_store_name = settings.DB_DATASTORE_NAME
    now = datetime.datetime.now()
    db_store_name = 'wm_%s%02d' % (now.year, now.month)
    if user:
        # only users in target-joins-uploader group will use the dataverse database
        if user.groups.filter(name=settings.DATAVERSE_GROUP_NAME).exists():
            db_store_name = settings.DB_DATAVERSE_NAME
    return db_store_name


def save(layer, base_file, user, overwrite = True, title=None,
         abstract=None, permissions=None, keywords = (), charset = 'ISO-8859-1', sldfile = None):
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
        msg = ((_('Could not open ') + '%s' + _('. Make sure you are using a valid file'))
                % (base_file))
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

    db_store_name = get_db_store_name(user)
    try:
        if settings.DB_DATASTORE and the_layer_type == FeatureType.resource_type:
            store = cat.get_store(db_store_name)
        else:
            store = cat.get_store(name)
    except geoserver.catalog.FailedRequestError, e:
        # There is no store, ergo the road is clear
        pass
    else:
        # If we get a store, we do the following:
        # Is it empty?
        if db_store_name != store.name:
            resources = cat.get_resources(store=store)
            if len(resources) == 0:
            # What should we do about that empty store?
                if overwrite:
                    # We can just delete it and recreate it later.
                    store.delete()
                else:
                    msg = (_('The layer exists and the overwrite parameter is ') +
                       '%s' % overwrite)
                    raise GeoNodeException(msg)
        else:
            # If our resource is already configured in the store it needs
            # to have the right resource type
            resource = cat.get_resource(name, store=store)
            if resource is not None:
                    msg = _('Name already in use and overwrite is False')
                    assert overwrite, msg
                    existing_type = resource.resource_type
                    if existing_type != the_layer_type:
                        msg =  ((_('Type of uploaded file') + ' %s (%s) ' +
                                _('does not match type of existing resource type ') +
                                '%s') % (name,
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
            def create_store_and_resource(name, data, user, overwrite, charset):
                cat.create_featurestore(name, data, overwrite=overwrite, charset=charset)
                featurestore = cat.get_store(name)
                return featurestore, cat.get_resource(name,store=featurestore)
    elif the_layer_type == Coverage.resource_type:
        logger.debug("Uploading raster layer: [%s]", base_file)
        def create_store_and_resource(name, data, user, overwrite, charset):
            cat.create_coveragestore(name, data, overwrite=overwrite)
            coverage_store = cat.get_store(name)
            return coverage_store, cat.get_resource(name,store=coverage_store)
    else:
        msg = ((_('The layer type is') + ' %s ' + _('but should be') +
               ' %s or %s') % (
                              the_layer_type,
                              FeatureType.resource_type,
                              Coverage.resource_type))
        logger.warn(msg)
        raise GeoNodeException(msg)

    # Step 4. Create the store in GeoServer
    logger.info('>>> Step 4. Starting upload of [%s] to GeoServer...', name)

    # Get the helper files if they exist
    files = get_files(base_file, sldfile)

    data = files

    #FIXME: DONT DO THIS
    #-------------------
    if 'shp' not in files and 'zip' not in files:
        main_file = files['base']
        data = main_file
    # ------------------

    # Step 5. Create the store in GeoServer
    logger.info('>>> Step 5. Creating a [%s] resource in GeoServer...', name)

    try:
        store, gs_resource = create_store_and_resource(name, data, user, overwrite=overwrite, charset=charset)
    except geoserver.catalog.UploadError, e:
        msg = ((_('Could not save the layer') + ' %s' +
                _(', there was an upload error:') + ' %s')
                % (name, _("Invalid/missing projection information in image")
                    if "Error auto-configuring coverage:null" in str(e) else
                    _("Your shapefile may contain reserved column names such as minx or maxy; try renaming them") if "Error occurred creating table" in str(e)
                    else str(e)))
        logger.warn(msg)
        e.args = (msg,)
        raise
    except geoserver.catalog.ConflictingDataError, e:
        # A datastore of this name already exists
        msg = ((_('GeoServer reported a conflict creating a store with name ') +
               '%s: "%s"' +
               _('. This should never happen because a brand new name '
               'should have been generated. But since it happened, '
               'try renaming the file or deleting the store in '
               'GeoServer.'))  % (name, str(e)))
        logger.warn(msg)
        e.args = (msg,)
        raise
    else:
        logger.debug('Finished upload of [%s] to GeoServer without '
                     'errors.', name)


    # Step 6. Create the resource in GeoServer
    logger.info('>>> Step 6. Generating the metadata for [%s] after '
                'successful import to GeoSever', name)

    # Verify the resource was created
    if gs_resource is not None:
        assert gs_resource.name == name
    else:
        msg = ((_('GeoNode encountered problems when creating layer') + ' %s.' +
               _('It cannot find the Layer that matches this Workspace.'
               'This is likely a bug in Geoserver,'
               'try renaming your files.')) % name)
        logger.warn(msg)
        raise GeoNodeException(msg)

    # Step 7. Make sure our data always has a valid projection

    logger.info('>>> Step 7. Making sure [%s] has a valid projection' % name)
    check_projection(name, gs_resource)

    # Step 8. Create the style and assign it to the created resource
    # FIXME: Put this in gsconfig.py
    logger.info('>>> Step 8. Creating style for [%s]' % name)
    publishing = cat.get_layer(name)

    if 'sld' in files:
        f = open(files['sld'], 'r')
        sld = f.read()
        f.close()
        try:
            sldxml = XML(sld)
            valid_url = re.compile(settings.VALID_SLD_LINKS)
            for elem in sldxml.iter(tag='{http://www.opengis.net/sld}OnlineResource'):
                if '{http://www.w3.org/1999/xlink}href' in elem.attrib:
                    link = elem.attrib['{http://www.w3.org/1999/xlink}href']
                    if valid_url.match(link) is None:
                        raise Exception(_("External images in your SLD file are not permitted.  Please contact us if you would like your SLD images hosted on %s") % (settings.SITENAME))
        except ParseError, e:
            msg =_('Your SLD file contains invalid XML')
            logger.warn("%s - %s" % (msg, str(e)))
            e.args = (msg,)

        try:
            stylename = name + "_".join([choice('qwertyuiopasdfghjklzxcvbnm0123456789') for i in range(4)])
            cat.create_style(stylename, sld)
            #FIXME: Should we use the fully qualified typename?
            if (overwrite):
                alternate_styles = publishing._get_alternate_styles()
                alternate_styles.append(cat.get_style(stylename))
                publishing._set_alternate_styles(alternate_styles)
            else:
                publishing.default_style = cat.get_style(stylename)
            cat.save(publishing)
        except geoserver.catalog.ConflictingDataError, e:
            msg = (_('There is already a style in GeoServer named ') +
               '"%s"' % (name))
            logger.warn(msg)
            e.args = (msg,)

    else:
        sld = get_sld_for(publishing)


        if sld is not None:
            stylename = name + "_".join([choice('qwertyuiopasdfghjklzxcvbnm0123456789') for i in range(6)])
            try:
                cat.create_style(stylename, sld)
            except geoserver.catalog.ConflictingDataError, e:
                msg = (_('There is already a style in GeoServer named ') +
                   '"%s"' % (stylename))
                logger.warn(msg)
                e.args = (msg,)
            #FIXME: Should we use the fully qualified typename?
            publishing.default_style = cat.get_style(stylename)
            cat.save(publishing)

    # Step 9. Create the Django record for the layer
    logger.info('>>> Step 9. Creating Django record for [%s]', name)
    # FIXME: Do this inside the layer object
    saved_layer = create_django_record(user, title, keywords, abstract, gs_resource, permissions)
    return saved_layer

def create_django_record(user, title, keywords, abstract, gs_resource, permissions):
    name = gs_resource.name
    typename = gs_resource.store.workspace.name + ':' + name
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

    if created:
        saved_layer.set_default_permissions()
        saved_layer.keywords.add(*keywords)

    try:
        # Step 9. Delete layer attributes if they no longer exist in an updated layer
        logger.info('>>> Step 11. Delete layer attributes if they no longer exist in an updated layer [%s]', name)
        attributes = LayerAttribute.objects.filter(layer=saved_layer)
        attrNames = saved_layer.attribute_names
        if attrNames is not None:
            for la in attributes:
                lafound = False
                for field, ftype in attrNames.iteritems():
                    if field == la.attribute:
                        lafound = True
                if not lafound:
                    logger.debug("Going to delete [%s] for [%s]", la.attribute, saved_layer.name)
                    la.delete()

        #
        # Step 10. Add new layer attributes if they dont already exist
        logger.info('>>> Step 10. Add new layer attributes if they dont already exist in an updated layer [%s]', name)
        if attrNames is not None:
            logger.debug("Attributes are not None")
            iter = 1
            mark_searchable = True
            for field, ftype in attrNames.iteritems():
                    if field is not None and  ftype.find("gml:") != 0:
                        las = LayerAttribute.objects.filter(layer=saved_layer, attribute=field)
                        if len(las) == 0:
                            la = LayerAttribute.objects.create(layer=saved_layer, attribute=field, attribute_label=field.title(), attribute_type=ftype, searchable=(ftype == "xsd:string" and mark_searchable), display_order = iter)
                            la.save()
                            if la.searchable:
                                mark_searchable = False
                            iter+=1
        else:
            logger.debug("No attributes found")

    except Exception, ex:
                    logger.debug("Attributes could not be saved:[%s]", str(ex))

    poc_contact, __ = Contact.objects.get_or_create(user=user,
                                           defaults={"name": user.username })
    author_contact, __ = Contact.objects.get_or_create(user=user,
                                           defaults={"name": user.username })

    logger.debug('Creating poc and author records for %s', poc_contact)

    saved_layer.poc = poc_contact
    saved_layer.metadata_author = author_contact

    saved_layer.save_to_geonetwork()

    # Step 11. Set default permissions on the newly created layer
    # FIXME: Do this as part of the post_save hook
    logger.info('>>> Step 11. Setting default permissions for [%s]', name)
    if permissions is not None:
        from geonode.maps.views import set_layer_permissions
        set_layer_permissions(saved_layer, permissions, True)

    # Step 12. Verify the layer was saved correctly and clean up if needed
    logger.info('>>> Step 12. Verifying the layer [%s] was created '
                'correctly' % name)

    # Verify the object was saved to the Django database
    try:
        Layer.objects.get(name=name)
    except Layer.DoesNotExist, e:
        msg = ((_('There was a problem saving the layer ') + '%s ' +
               _('Error is: ') + '%s') % (name, str(e)))
        logger.exception(msg)
        logger.debug('Attempting to clean up after failed save for layer '
                     '[%s]', name)
        # Since the layer creation was not successful, we need to clean up
        cleanup(name, layer_uuid)
        raise GeoNodeException(msg)

    # Verify it is correctly linked to GeoServer and GeoNetwork
    try:
        # FIXME: Implement a verify method that makes sure it was
        # saved in both GeoNetwork and GeoServer
        saved_layer.verify()
    except NotImplementedError, e:
        logger.exception('>>> FIXME: Please, if you can write python code, '
                         'implement "verify()" '
                         'method in geonode.maps.models.Layer')
    except GeoNodeException, e:
        msg = (_('The layer was not correctly saved to '
               'GeoNetwork/GeoServer. Error is: ') + str(e))
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

def get_valid_user(user=None):
    """Gets the default user or creates it if it does not exist
    """
    if user is None:
        theuser = get_default_user()
    elif isinstance(user, basestring):
        theuser = User.objects.get(username=user)
    elif user.is_anonymous():
        raise GeoNodeException('The user uploading files must not '
                               'be anonymous')
    else:
        theuser = user

    #FIXME: Pass a user in the unit tests that is not yet saved ;)
    assert isinstance(theuser, User)

    return theuser


def check_geonode_is_up():
    """Verifies all of geonetwork, geoserver and the django server are running,
       this is needed to be able to upload.
    """
    try:
        Layer.objects.gs_catalog.get_workspaces()
    except:
        msg = ((_('Cannot connect to the GeoServer at ') + '%s\n' +
               _('Please make sure you have started GeoNode.')) % settings.GEOSERVER_BASE_URL)
        raise GeoNodeException(msg)

    try:
        Layer.objects.gn_catalog.login()
    except:
        msg = ((_('Cannot connect to the GeoNetwork at ') + '%s\n' +
            _('Please make sure you have started GeoNetwork.'))
            % settings.GEONETWORK_BASE_URL)
        raise GeoNodeException(msg)

def file_upload(filename, user=None, title=None, skip=True, overwrite=False, keywords=(), charset='ISO-8859-1'):
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

    new_layer = save(layer, filename, theuser, overwrite, title, keywords=keywords, charset=charset)

    return new_layer


def upload(incoming, user=None, overwrite=True, keywords = (), skip=True, ignore_errors=True, verbosity=1, console=sys.stdout, charset='ISO-8859-1'):
    """Upload a directory of spatial data files to GeoNode

       This function also verifies that each layer is in GeoServer.

       Supported extensions are: .shp, .tif, and .zip (of a shapfile).
       It catches GeoNodeExceptions and gives a report per file
    """
    if verbosity > 1:
        print >> console, "Verifying that GeoNode is running ..."
    check_geonode_is_up()

    potential_files = []
    if os.path.isfile(incoming):
        ___, short_filename = os.path.split(incoming)
        basename, extension = os.path.splitext(short_filename)
        filename = incoming

        if extension in ['.tif', '.shp', '.zip']:
            potential_files.append((basename, filename))

    elif not os.path.isdir(incoming):
        msg = ((_('Please pass a filename or a directory name as the "incoming" '
               'parameter, instead of ') + '%s: %s') % (incoming, type(incoming)))
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
                    potential_files.append((basename, filename))

    # After gathering the list of potential files, let's process them one by one.
    number = len(potential_files)
    if verbosity > 1:
        msg =  ('%d' + _("potential layers found, importing now ...")) % number
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
        else:
            save_it = True

        if save_it:
            try:
                layer = file_upload(filename,
                                    user=user,
                                    title=basename,
                                    overwrite=overwrite,
                                    keywords=keywords,
                                    charset=charset
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
                        msg = _("Stopping process because --ignore-errors was not set and an error was found.")
                        print >> sys.stderr, msg
                        raise Exception('Failed to process %s' % filename, e), None, sys.exc_info()[2]

        msg = ("[%s] " + _('Layer for ') + "'%s' (%d/%d)") % (status, filename, i+1, number)
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

def _create_db_featurestore(name, data, user, overwrite = False, charset = None):
    """Create a database store then use it to import a shapefile.

    If the import into the database fails then delete the store
    (and delete the PostGIS table for it).
    """
    db_store_name = get_db_store_name(user)
    cat = Layer.objects.gs_catalog
    try:
        ds = cat.get_store(db_store_name)
    except FailedRequestError:
        ds = cat.create_datastore(db_store_name)
        ds.connection_parameters.update(
            host=settings.DB_DATASTORE_HOST,
            port=settings.DB_DATASTORE_PORT,
            database=db_store_name,
            user=settings.DB_DATASTORE_USER,
            passwd=settings.DB_DATASTORE_PASSWORD,
            dbtype=settings.DB_DATASTORE_TYPE)
        cat.save(ds)
        ds = cat.get_store(db_store_name)
    try:
        cat.add_data_to_store(ds, name, data, overwrite=overwrite, charset=charset)
        return ds, cat.get_resource(name, store=ds)
    except:
        store_params = ds.connection_parameters
        if store_params['dbtype'] and store_params['dbtype'] == 'postgis':
            delete_from_postgis(name, db_store_name)
        else:
            cat.delete(ds, purge=True)
        raise

def forward_mercator(lonlat):
    """
        Given geographic coordinates, return a x,y tuple in spherical mercator.

        If the lat value is out of range, -inf will be returned as the y value
    """
    x = lonlat[0] * 20037508.34 / 180
    n = math.tan((90 + lonlat[1]) * math.pi / 360)
    if n <= 0:
        y = float("-inf")
    else:
        y = math.log(n) / math.pi * 20037508.34
    return (x, y)

def inverse_mercator(xy):
    """
        Given coordinates in spherical mercator, return a lon,lat tuple.
    """
    lon = (xy[0] / 20037508.34) * 180
    lat = (xy[1] / 20037508.34) * 180
    lat = 180/math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
    return (lon, lat)

def check_projection(name, resource):
    # Get a short handle to the gsconfig geoserver catalog
    cat = Layer.objects.gs_catalog

    try:
        if resource.latlon_bbox is None:
            box = resource.native_bbox[:4]
            minx, maxx, miny, maxy = [float(a) for a in box]
            if -180 <= minx <= 180 and -180 <= maxx <= 180 and\
               -90  <= miny <= 90  and -90  <= maxy <= 90:
                logger.warn('GeoServer failed to detect the projection for layer '
                            '[%s]. Guessing EPSG:4326', name)
                # If GeoServer couldn't figure out the projection, we just
                # assume it's lat/lon to avoid a bad GeoServer configuration

                resource.latlon_bbox = resource.native_bbox
                resource.projection = "EPSG:4326"
                cat.save(resource)
            else:
                msg = ((_('GeoServer failed to detect the projection for layer ') +
                       '[%s].' +
                       _('It doesn\'t look like EPSG:4326, so backing out the layer.')))
                logger.warn(msg, name)
                cascading_delete(cat, resource)
                raise GeoNodeException(msg % name)
    except:
        msg = ((_('GeoServer failed to read the layer projection for') + ' [%s] ' +
               _('so backing out the layer.')))
        cascading_delete(cat, resource)
        raise GeoNodeException(msg % name)
