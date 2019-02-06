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

"""Utilities for managing GeoNode layers
"""

# Standard Modules
import re
import os
import glob
import sys
import logging

from geonode.maps.models import Map
from osgeo import gdal, osr

# Django functionality
from django.contrib.auth import get_user_model
from django.template.defaultfilters import slugify
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage as storage
from django.core.files import File
from django.conf import settings
from django.db import transaction
from django.db.models import Q

# Geonode functionality
from geonode import GeoNodeException, geoserver, qgis_server
from geonode.people.utils import get_valid_user
from geonode.layers.models import Layer, UploadSession, LayerFile
from geonode.base.models import Link, SpatialRepresentationType,  \
    TopicCategory, Region, License, ResourceBase
from geonode.layers.models import shp_exts, csv_exts, vec_exts, cov_exts
from geonode.layers.metadata import set_metadata
from geonode.utils import (http_client, check_ogc_backend,
                           unzip_file, extract_tarfile)
from ..geoserver.helpers import (ogc_server_settings,
                                 _prepare_thumbnail_body_from_opts)

import tarfile

from zipfile import ZipFile, is_zipfile

from datetime import datetime

logger = logging.getLogger('geonode.layers.utils')

_separator = '\n' + ('-' * 100) + '\n'


def _clean_string(
        str,
        regex=r"(^[^a-zA-Z\._]+)|([^a-zA-Z\._0-9]+)",
        replace="_"):
    """
    Replaces a string that matches the regex with the replacement.
    """
    regex = re.compile(regex)

    if str[0].isdigit():
        str = replace + str

    return regex.sub(replace, str)


def resolve_regions(regions):
    regions_resolved = []
    regions_unresolved = []
    if regions:
        if len(regions) > 0:
            for region in regions:
                try:
                    region_resolved = Region.objects.get(
                        Q(name__iexact=region) | Q(code__iexact=region))
                    regions_resolved.append(region_resolved)
                except ObjectDoesNotExist:
                    regions_unresolved.append(region)

    return regions_resolved, regions_unresolved


def get_files(filename):
    """Converts the data to Shapefiles or Geotiffs and returns
       a dictionary with all the required files
    """
    files = {}

    # Verify if the filename is in ascii format.
    try:
        filename.decode('ascii')
    except UnicodeEncodeError:
        msg = "Please use only characters from the english alphabet for the filename. '%s' is not yet supported." \
            % os.path.basename(filename).encode('UTF-8')
        raise GeoNodeException(msg)

    # Let's unzip the filname in case it is a ZIP file
    import tempfile
    import zipfile
    from geonode.utils import unzip_file
    if zipfile.is_zipfile(filename):
        tempdir = tempfile.mkdtemp()
        filename = unzip_file(filename,
                              '.shp', tempdir=tempdir)
        if not filename:
            # We need to iterate files as filename could be the zipfile
            import ntpath
            from geonode.upload.utils import _SUPPORTED_EXT
            file_basename, file_ext = ntpath.splitext(filename)
            for item in os.listdir(tempdir):
                item_basename, item_ext = ntpath.splitext(item)
                if ntpath.basename(item_basename) == ntpath.basename(file_basename) and (
                        item_ext.lower() in _SUPPORTED_EXT):
                    filename = os.path.join(tempdir, item)
                    break

    # Make sure the file exists.
    if not os.path.exists(filename):
        msg = ('Could not open %s. Make sure you are using a '
               'valid file' % filename)
        logger.warn(msg)
        raise GeoNodeException(msg)

    base_name, extension = os.path.splitext(filename)
    # Replace special characters in filenames - []{}()
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

    elif extension.lower() in cov_exts:
        files[extension.lower().replace('.', '')] = filename

    # Only for GeoServer
    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        matches = glob.glob(glob_name + ".[sS][lL][dD]")
        if len(matches) == 1:
            files['sld'] = matches[0]
        elif len(matches) > 1:
            msg = ('Multiple style files (sld) for %s exist; they need to be '
                   'distinct by spelling and not just case.') % filename
            raise GeoNodeException(msg)

    matches = glob.glob(glob_name + ".[xX][mM][lL]")

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

    # Only for QGIS Server
    if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
        matches = glob.glob(glob_name + ".[qQ][mM][lL]")
        logger.debug('Checking QML file')
        logger.debug('Number of matches QML file : %s' % len(matches))
        logger.debug('glob name: %s' % glob_name)
        if len(matches) == 1:
            files['qml'] = matches[0]
        elif len(matches) > 1:
            msg = ('Multiple style files (qml) for %s exist; they need to be '
                   'distinct by spelling and not just case.') % filename
            raise GeoNodeException(msg)

        # Provides json files for additional extra data
        matches = glob.glob(glob_name + ".[jJ][sS][oO][nN]")
        logger.debug('Checking JSON File')
        logger.debug(
            'Number of matches JSON file : %s' % len(matches))
        logger.debug('glob name: %s' % glob)

        if len(matches) == 1:
            files['json'] = matches[0]
        elif len(matches) > 1:
            msg = ('Multiple json files (json) for %s exist; they need to be '
                   'distinct by spelling and not just case.') % filename
            raise GeoNodeException(msg)

    return files


def layer_type(filename):
    """Finds out if a filename is a Feature or a Vector
       returns a gsconfig resource_type string
       that can be either 'featureType' or 'coverage'
    """
    base_name, extension = os.path.splitext(filename)

    if extension.lower() == '.zip':
        zf = ZipFile(filename)
        # ZipFile doesn't support with statement in 2.6, so don't do it
        try:
            for n in zf.namelist():
                b, e = os.path.splitext(n.lower())
                if e in shp_exts or e in cov_exts or e in csv_exts:
                    extension = e
        finally:
            zf.close()

    if extension.lower() == '.tar' or filename.endswith('.tar.gz'):
        tf = tarfile.open(filename)
        # TarFile doesn't support with statement in 2.6, so don't do it
        try:
            for n in tf.getnames():
                b, e = os.path.splitext(n.lower())
                if e in shp_exts or e in cov_exts or e in csv_exts:
                    extension = e
        finally:
            tf.close()

    if extension.lower() in vec_exts:
        return 'vector'
    elif extension.lower() in cov_exts:
        return 'raster'
    else:
        msg = ('Saving of extension [%s] is not implemented' % extension)
        raise GeoNodeException(msg)


def get_valid_name(layer_name):
    """
    Create a brand new name
    """
    name = _clean_string(layer_name)
    proposed_name = name
    count = 1
    while Layer.objects.filter(name=proposed_name).exists():
        proposed_name = "%s_%d" % (name, count)
        count = count + 1
        logger.warning('Requested name already used; adjusting name '
                       '[%s] => [%s]', layer_name, proposed_name)
    else:
        logger.debug("Using name as requested")

    return proposed_name


def get_valid_layer_name(layer, overwrite):
    """Checks if the layer is a string and fetches it from the database.
    """
    # The first thing we do is get the layer name string
    if isinstance(layer, Layer):
        layer_name = layer.name
    elif isinstance(layer, basestring):
        layer_name = str(layer)
    else:
        msg = ('You must pass either a filename or a GeoNode layer object')
        raise GeoNodeException(msg)

    if overwrite:
        return layer_name
    else:
        return get_valid_name(layer_name)


def get_default_user():
    """Create a default user
    """
    superusers = get_user_model().objects.filter(
        is_superuser=True).order_by('id')
    if superusers.count() > 0:
        # Return the first created superuser
        return superusers[0]
    else:
        raise GeoNodeException('You must have an admin account configured '
                               'before importing data. '
                               'Try: django-admin.py createsuperuser')


def is_vector(filename):
    __, extension = os.path.splitext(filename)

    if extension in vec_exts:
        return True
    else:
        return False


def is_raster(filename):
    __, extension = os.path.splitext(filename)

    if extension in cov_exts:
        return True
    else:
        return False


def get_resolution(filename):
    gtif = gdal.Open(filename)
    gt = gtif.GetGeoTransform()
    __, resx, __, __, __, resy = gt
    resolution = '%s %s' % (resx, resy)
    return resolution


def get_bbox(filename):
    """Return bbox in the format [xmin,xmax,ymin,ymax]."""
    from django.contrib.gis.gdal import DataSource, SRSException
    srid = None
    bbox_x0, bbox_y0, bbox_x1, bbox_y1 = None, None, None, None

    if is_vector(filename):
        y_min = -90
        y_max = 90
        x_min = -180
        x_max = 180
        datasource = DataSource(filename)
        layer = datasource[0]
        bbox_x0, bbox_y0, bbox_x1, bbox_y1 = layer.extent.tuple
        srs = layer.srs
        try:
            if not srs:
                raise GeoNodeException('Invalid Projection. Layer is missing CRS!')
            srs.identify_epsg()
        except SRSException:
            pass
        epsg_code = srs.srid
        # can't find epsg code, then check if bbox is within the 4326 boundary
        if epsg_code is None and (x_min <= bbox_x0 <= x_max and
                                  x_min <= bbox_x1 <= x_max and
                                  y_min <= bbox_y0 <= y_max and
                                  y_min <= bbox_y1 <= y_max):
            # set default epsg code
            epsg_code = '4326'
        elif epsg_code is None:
            # otherwise, stop the upload process
            raise GeoNodeException(
                "Invalid Layers. "
                "Needs an authoritative SRID in its CRS to be accepted")

        # eliminate default EPSG srid as it will be added when this function returned
        srid = epsg_code if epsg_code else '4326'
    elif is_raster(filename):
        gtif = gdal.Open(filename)
        gt = gtif.GetGeoTransform()
        prj = gtif.GetProjection()
        srs = osr.SpatialReference(wkt=prj)
        cols = gtif.RasterXSize
        rows = gtif.RasterYSize

        ext = []
        xarr = [0, cols]
        yarr = [0, rows]

        # Get the extent.
        for px in xarr:
            for py in yarr:
                x = gt[0] + (px * gt[1]) + (py * gt[2])
                y = gt[3] + (px * gt[4]) + (py * gt[5])
                ext.append([x, y])

            yarr.reverse()

        # ext has four corner points, get a bbox from them.
        # order is important, so make sure min and max is correct.
        bbox_x0 = min(ext[0][0], ext[2][0])
        bbox_y0 = min(ext[0][1], ext[2][1])
        bbox_x1 = max(ext[0][0], ext[2][0])
        bbox_y1 = max(ext[0][1], ext[2][1])
        srid = srs.GetAuthorityCode(None) if srs else '4326'

    return [bbox_x0, bbox_x1, bbox_y0, bbox_y1, "EPSG:%s" % str(srid)]


def file_upload(filename,
                name=None,
                user=None,
                title=None,
                abstract=None,
                license=None,
                category=None,
                keywords=None,
                regions=None,
                date=None,
                skip=True,
                overwrite=False,
                charset='UTF-8',
                is_approved=True,
                is_published=True,
                metadata_uploaded_preserve=False,
                metadata_upload_form=False):
    """Saves a layer in GeoNode asking as little information as possible.
       Only filename is required, user and title are optional.

    :return: Uploaded layer
    :rtype: Layer
    """
    if keywords is None:
        keywords = []
    if regions is None:
        regions = []

    # Get a valid user
    theuser = get_valid_user(user)

    # Create a new upload session
    upload_session = UploadSession.objects.create(user=theuser)

    # Get all the files uploaded with the layer
    files = get_files(filename)

    # Set a default title that looks nice ...
    if title is None:
        basename = os.path.splitext(os.path.basename(filename))[0]
        title = basename.title().replace('_', ' ')

    # Create a name from the title if it is not passed.
    if name is None:
        name = slugify(title).replace('-', '_')
    elif not overwrite:
        name = slugify(name)  # assert that name is slugified

    if license is not None:
        licenses = License.objects.filter(
            Q(name__iexact=license) |
            Q(abbreviation__iexact=license) |
            Q(url__iexact=license) |
            Q(description__iexact=license))
        if len(licenses) == 1:
            license = licenses[0]
        else:
            license = None

    if category is not None:
        try:
            categories = TopicCategory.objects.filter(
                Q(identifier__iexact=category) |
                Q(gn_description__iexact=category))
            if len(categories) == 1:
                category = categories[0]
            else:
                category = None
        except BaseException:
            pass

    # Generate a name that is not taken if overwrite is False.
    valid_name = get_valid_layer_name(name, overwrite)

    # Add them to the upload session (new file fields are created).
    assigned_name = None
    for type_name, fn in files.items():
        with open(fn, 'rb') as f:
            upload_session.layerfile_set.create(
                name=type_name, file=File(
                    f, name='%s.%s' %
                    (assigned_name or valid_name, type_name)))
            # save the system assigned name for the remaining files
            if not assigned_name:
                the_file = upload_session.layerfile_set.all()[0].file.name
                assigned_name = os.path.splitext(os.path.basename(the_file))[0]

    # Get a bounding box
    bbox_x0, bbox_x1, bbox_y0, bbox_y1, srid = get_bbox(filename)
    if srid:
        srid_url = "http://www.spatialreference.org/ref/" + srid.replace(':', '/').lower() + "/"  # noqa

    # by default, if RESOURCE_PUBLISHING=True then layer.is_published
    # must be set to False
    if not overwrite:
        if settings.RESOURCE_PUBLISHING or settings.ADMIN_MODERATE_UPLOADS:
            is_approved = False
            is_published = False

    defaults = {
        'upload_session': upload_session,
        'title': title,
        'abstract': abstract,
        'owner': user,
        'charset': charset,
        'bbox_x0': bbox_x0,
        'bbox_x1': bbox_x1,
        'bbox_y0': bbox_y0,
        'bbox_y1': bbox_y1,
        'srid': srid,
        'is_approved': is_approved,
        'is_published': is_published,
        'license': license,
        'category': category
    }

    # set metadata
    if 'xml' in files:
        with open(files['xml']) as f:
            xml_file = f.read()

        defaults['metadata_uploaded'] = True

        defaults['metadata_uploaded_preserve'] = metadata_uploaded_preserve

        # get model properties from XML
        identifier, vals, regions, keywords = set_metadata(xml_file)

        if defaults['metadata_uploaded_preserve']:
            defaults['metadata_xml'] = xml_file

            defaults['uuid'] = identifier

        for key, value in vals.items():
            if key == 'spatial_representation_type':
                value = SpatialRepresentationType(identifier=value)
            elif key == 'topic_category':
                value, created = TopicCategory.objects.get_or_create(
                    identifier=value.lower(),
                    defaults={'description': '', 'gn_description': value})
                key = 'category'

                defaults[key] = value
            else:
                defaults[key] = value

    regions_resolved, regions_unresolved = resolve_regions(regions)
    keywords.extend(regions_unresolved)

    if getattr(settings, 'NLP_ENABLED', False):
        try:
            from geonode.contrib.nlp.utils import nlp_extract_metadata_dict
            nlp_metadata = nlp_extract_metadata_dict({
                'title': defaults.get('title', None),
                'abstract': defaults.get('abstract', None),
                'purpose': defaults.get('purpose', None)})
            if nlp_metadata:
                regions_resolved.extend(nlp_metadata.get('regions', []))
                keywords.extend(nlp_metadata.get('keywords', []))
        except BaseException:
            logger.error("NLP extraction failed.")

    # If it is a vector file, create the layer in postgis.
    if is_vector(filename):
        defaults['storeType'] = 'dataStore'

    # If it is a raster file, get the resolution.
    if is_raster(filename):
        defaults['storeType'] = 'coverageStore'

    # Create a Django object.
    created = False
    layer = None
    with transaction.atomic():
        try:
            if overwrite:
                try:
                    layer = Layer.objects.get(name=valid_name)
                except Layer.DoesNotExist:
                    layer = None
            if not layer:
                if not metadata_upload_form:
                    layer, created = Layer.objects.get_or_create(
                        name=valid_name,
                        workspace=settings.DEFAULT_WORKSPACE,
                        defaults=defaults
                    )
                elif identifier:
                    layer, created = Layer.objects.get_or_create(
                        uuid=identifier,
                        defaults=defaults
                    )
        except BaseException:
            raise

    # Delete the old layers if overwrite is true
    # and the layer was not just created
    # process the layer again after that by
    # doing a layer.save()
    if not created and overwrite:
        # update with new information
        defaults['upload_session'] = upload_session

        defaults['title'] = defaults.get('title', None) or layer.title

        defaults['abstract'] = defaults.get('abstract', None) or layer.abstract

        defaults['bbox_x0'] = defaults.get('bbox_x0', None) or layer.bbox_x0

        defaults['bbox_x1'] = defaults.get('bbox_x1', None) or layer.bbox_x1

        defaults['bbox_y0'] = defaults.get('bbox_y0', None) or layer.bbox_y0

        defaults['bbox_y1'] = defaults.get('bbox_y1', None) or layer.bbox_y1

        defaults['is_approved'] = defaults.get(
            'is_approved', is_approved) or layer.is_approved

        defaults['is_published'] = defaults.get(
            'is_published', is_published) or layer.is_published

        defaults['license'] = defaults.get('license', None) or layer.license

        defaults['category'] = defaults.get('category', None) or layer.category

        try:
            Layer.objects.filter(id=layer.id).update(**defaults)
            layer.refresh_from_db()
        except Layer.DoesNotExist:
            import traceback
            tb = traceback.format_exc()
            logger.error(tb)
            raise

        # Pass the parameter overwrite to tell whether the
        # geoserver_post_save_signal should upload the new file or not
        layer.overwrite = overwrite

        # Blank out the store if overwrite is true.
        # geoserver_post_save_signal should upload the new file if needed
        layer.store = '' if overwrite else layer.store
        layer.save()

        if upload_session:
            upload_session.resource = layer
            upload_session.processed = True
            upload_session.save()

        # set SLD
        # if 'sld' in files:
        #     sld = None
        #     with open(files['sld']) as f:
        #         sld = f.read()
        #     if sld:
        #         set_layer_style(layer, layer.alternate, sld, base_file=files['sld'])

    # Assign the keywords (needs to be done after saving)
    keywords = list(set(keywords))
    if keywords:
        if len(keywords) > 0:
            if not layer.keywords:
                layer.keywords = keywords
            else:
                layer.keywords.add(*keywords)

    # Assign the regions (needs to be done after saving)
    regions_resolved = list(set(regions_resolved))
    if regions_resolved:
        if len(regions_resolved) > 0:
            if not layer.regions:
                layer.regions = regions_resolved
            else:
                layer.regions.clear()
                layer.regions.add(*regions_resolved)

    # Assign and save the charset using the Layer class' object (layer)
    if charset != 'UTF-8':
        layer.charset = charset
        layer.save()

    to_update = {}
    if defaults.get('title', title) is not None:
        to_update['title'] = defaults.get('title', title)
    if defaults.get('abstract', abstract) is not None:
        to_update['abstract'] = defaults.get('abstract', abstract)
    if defaults.get('date', date) is not None:
        to_update['date'] = defaults.get('date',
                                         datetime.strptime(date, '%Y-%m-%d %H:%M:%S') if date else None)
    if defaults.get('license', license) is not None:
        to_update['license'] = defaults.get('license', license)
    if defaults.get('category', category) is not None:
        to_update['category'] = defaults.get('category', category)

    # Update ResourceBase
    if not to_update:
        pass
    else:
        try:
            ResourceBase.objects.filter(
                id=layer.resourcebase_ptr.id).update(
                **to_update)
            Layer.objects.filter(id=layer.id).update(**to_update)

            # Refresh from DB
            layer.refresh_from_db()
        except BaseException:
            import traceback
            tb = traceback.format_exc()
            logger.error(tb)

    return layer


def upload(incoming, user=None, overwrite=False,
           name=None, title=None, abstract=None, date=None,
           license=None,
           category=None, keywords=None, regions=None,
           skip=True, ignore_errors=True,
           verbosity=1, console=None,
           private=False, metadata_uploaded_preserve=False,
           charset='UTF-8'):
    """Upload a directory of spatial data files to GeoNode

       This function also verifies that each layer is in GeoServer.

       Supported extensions are: .shp, .tif, .tar, .tar.gz, and .zip (of a shapefile).
       It catches GeoNodeExceptions and gives a report per file
    """
    if verbosity > 1:
        print >> console, "Verifying that GeoNode is running ..."

    if console is None:
        console = open(os.devnull, 'w')

    potential_files = []
    if os.path.isfile(incoming):
        ___, short_filename = os.path.split(incoming)
        basename, extension = os.path.splitext(short_filename)
        filename = incoming

        if extension in ['.tif', '.shp', '.tar', '.zip']:
            potential_files.append((basename, filename))
        elif short_filename.endswith('.tar.gz'):
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
                if extension in ['.tif', '.shp', '.tar', '.zip']:
                    potential_files.append((basename, filename))
                elif short_filename.endswith('.tar.gz'):
                    potential_files.append((basename, filename))

    # After gathering the list of potential files,
    # let's process them one by one.
    number = len(potential_files)
    if verbosity > 1:
        msg = "Found %d potential layers." % number
        print >> console, msg

    if (number > 1) and (name is not None):
        msg = 'Failed to process.  Cannot specify name with multiple imports.'
        raise Exception(msg)

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
                if is_zipfile(filename):
                    filename = unzip_file(filename)

                if tarfile.is_tarfile(filename):
                    filename = extract_tarfile(filename)

                layer = file_upload(
                    filename,
                    name=name,
                    title=title,
                    abstract=abstract,
                    date=date,
                    user=user,
                    overwrite=overwrite,
                    license=license,
                    category=category,
                    keywords=keywords,
                    regions=regions,
                    metadata_uploaded_preserve=metadata_uploaded_preserve,
                    charset=charset)
                if not existed:
                    status = 'created'
                else:
                    status = 'updated'
                if private and user:
                    perm_spec = {
                        "users": {
                            "AnonymousUser": [],
                            user.username: [
                                "change_resourcebase_metadata",
                                "change_layer_data",
                                "change_layer_style",
                                "change_resourcebase",
                                "delete_resourcebase",
                                "change_resourcebase_permissions",
                                "publish_resourcebase"]},
                        "groups": {}}
                    layer.set_permissions(perm_spec)

                if getattr(settings, 'SLACK_ENABLED', False):
                    try:
                        from geonode.contrib.slack.utils import build_slack_message_layer, send_slack_messages
                        send_slack_messages(
                            build_slack_message_layer(
                                ("layer_new" if status == "created" else "layer_edit"), layer))
                    except BaseException:
                        logger.error("Could not send slack message.")

            except Exception as e:
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


def create_thumbnail(instance, thumbnail_remote_url, thumbnail_create_url=None,
                     check_bbox=False, ogc_client=None, overwrite=False,
                     width=240, height=200):
    thumbnail_dir = os.path.join(settings.MEDIA_ROOT, 'thumbs')
    if not os.path.exists(thumbnail_dir):
        os.makedirs(thumbnail_dir)
    thumbnail_name = None
    if isinstance(instance, Layer):
        thumbnail_name = 'layer-%s-thumb.png' % instance.uuid
    elif isinstance(instance, Map):
        thumbnail_name = 'map-%s-thumb.png' % instance.uuid
    thumbnail_path = os.path.join(thumbnail_dir, thumbnail_name)
    if overwrite or not storage.exists(thumbnail_path):
        BBOX_DIFFERENCE_THRESHOLD = 1e-5

        if not thumbnail_create_url:
            thumbnail_create_url = thumbnail_remote_url

        if check_bbox:
            # Check if the bbox is invalid
            valid_x = (
                float(
                    instance.bbox_x0) -
                float(
                    instance.bbox_x1)) ** 2 > BBOX_DIFFERENCE_THRESHOLD
            valid_y = (
                float(
                    instance.bbox_y1) -
                float(
                    instance.bbox_y0)) ** 2 > BBOX_DIFFERENCE_THRESHOLD
        else:
            valid_x = True
            valid_y = True

        image = None

        if valid_x and valid_y:
            Link.objects.get_or_create(resource=instance.get_self_resource(),
                                       url=thumbnail_remote_url,
                                       defaults=dict(
                                           extension='png',
                                           name="Remote Thumbnail",
                                           mime='image/png',
                                           link_type='image',
            )
            )
            ResourceBase.objects.filter(id=instance.id) \
                .update(thumbnail_url=thumbnail_remote_url)

            # Download thumbnail and save it locally.
            if not ogc_client and not check_ogc_backend(geoserver.BACKEND_PACKAGE):
                ogc_client = http_client

            if ogc_client:
                try:
                    params = {
                        'width': width,
                        'height': height
                    }
                    # Add the bbox param only if the bbox is different to [None, None,
                    # None, None]
                    if None not in instance.bbox:
                        params['bbox'] = instance.bbox_string
                        params['crs'] = instance.srid

                    _p = "&".join("%s=%s" % item for item in params.items())
                    resp, image = ogc_client.request(thumbnail_create_url + '&' + _p)
                    if 'ServiceException' in image or \
                       resp.status < 200 or resp.status > 299:
                        msg = 'Unable to obtain thumbnail: %s' % image
                        raise Exception(msg)
                except BaseException:
                    import traceback
                    logger.debug(traceback.format_exc())

                    # Replace error message with None.
                    image = None
            elif check_ogc_backend(geoserver.BACKEND_PACKAGE) and instance.bbox:
                instance_bbox = instance.bbox[0:4]
                request_body = {
                    'bbox': [str(coord) for coord in instance_bbox],
                    'srid': instance.srid,
                    'width': width,
                    'height': height
                }

                if thumbnail_create_url:
                    request_body['thumbnail_create_url'] = thumbnail_create_url
                elif instance.alternate:
                    request_body['layers'] = instance.alternate

                image = _prepare_thumbnail_body_from_opts(request_body)

            if image is not None:
                instance.save_thumbnail(thumbnail_name, image=image)
            else:
                msg = 'Unable to obtain thumbnail for: %s' % instance
                logger.error(msg)
                # raise Exception(msg)


# this is the original implementation of create_gs_thumbnail()
def create_gs_thumbnail_geonode(instance, overwrite=False, check_bbox=False):
    """
    Create a thumbnail with a GeoServer request.
    """
    if isinstance(instance, Map):
        local_layers = []
        # a map could be empty!
        if not instance.layers:
            return
        for layer in instance.layers:
            if layer.local:
                local_layers.append(layer.name)
        layers = ",".join(local_layers).encode('utf-8')
    else:
        layers = instance.alternate.encode('utf-8')

    wms_endpoint = getattr(ogc_server_settings, "WMS_ENDPOINT") or 'ows'
    wms_version = getattr(ogc_server_settings, "WMS_VERSION") or '1.1.1'
    wms_format = getattr(ogc_server_settings, "WMS_FORMAT") or 'image/png8'

    params = {
        'service': 'WMS',
        'version': wms_version,
        'request': 'GetMap',
        'layers': layers,
        'format': wms_format,
        # 'TIME': '-99999999999-01-01T00:00:00.0Z/99999999999-01-01T00:00:00.0Z'
    }

    # Avoid using urllib.urlencode here because it breaks the url.
    # commas and slashes in values get encoded and then cause trouble
    # with the WMS parser.
    _p = "&".join("%s=%s" % item for item in params.items())

    import posixpath
    thumbnail_remote_url = posixpath.join(
        ogc_server_settings.PUBLIC_LOCATION,
        wms_endpoint) + "?" + _p
    thumbnail_create_url = posixpath.join(
        ogc_server_settings.LOCATION,
        wms_endpoint) + "?" + _p
    create_thumbnail(instance, thumbnail_remote_url, thumbnail_create_url,
                     overwrite=overwrite, check_bbox=check_bbox)


def delete_orphaned_layers():
    """Delete orphaned layer files."""
    layer_path = os.path.join(settings.MEDIA_ROOT, 'layers')
    for filename in os.listdir(layer_path):
        fn = os.path.join(layer_path, filename)
        if LayerFile.objects.filter(file__icontains=filename).count() == 0:
            logger.info('Removing orphan layer file %s' % fn)
            try:
                os.remove(fn)
            except OSError:
                logger.info('Could not delete file %s' % fn)
