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
import string
import sys
import json
import logging
import tarfile

from datetime import datetime

from osgeo import gdal, osr, ogr
from zipfile import ZipFile, is_zipfile
from random import choice

# Django functionality
from django.conf import settings
from django.db.models import Q
from django.db import IntegrityError, transaction
from django.core.files import File
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.template.defaultfilters import slugify
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage as storage
from django.utils.translation import ugettext as _

# Geonode functionality
from geonode import GeoNodeException, geoserver
from geonode.people.utils import get_valid_user
from geonode.layers.models import UploadSession, LayerFile
from geonode.base.models import SpatialRepresentationType,  \
    TopicCategory, Region, License, ResourceBase
from geonode.layers.models import shp_exts, csv_exts, vec_exts, cov_exts, Layer
from geonode.layers.metadata import set_metadata
from geonode.upload.utils import _fixup_base_file
from geonode.utils import (check_ogc_backend,
                           unzip_file,
                           extract_tarfile)

READ_PERMISSIONS = [
    'view_resourcebase'
]
WRITE_PERMISSIONS = [
    'change_layer_data',
    'change_layer_style',
    'change_resourcebase_metadata'
]
DOWNLOAD_PERMISSIONS = [
    'download_resourcebase'
]
OWNER_PERMISSIONS = [
    'change_resourcebase',
    'delete_resourcebase',
    'change_resourcebase_permissions',
    'publish_resourcebase'
]

logger = logging.getLogger('geonode.layers.utils')

_separator = f"\n{'-' * 100}\n"


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
        filename.encode('ascii')
    except UnicodeEncodeError:
        msg = f"Please use only characters from the english alphabet for the filename. '{os.path.basename(filename).encode('UTF-8', 'strict')}' is not yet supported."
        raise GeoNodeException(msg)

    # Let's unzip the filname in case it is a ZIP file
    import tempfile
    from geonode.utils import unzip_file
    if is_zipfile(filename):
        tempdir = tempfile.mkdtemp(dir=settings.STATIC_ROOT)
        _filename = unzip_file(filename,
                               '.shp', tempdir=tempdir)
        if not _filename:
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
        else:
            filename = _filename

    # Make sure the file exists.
    if not os.path.exists(filename):
        msg = f'Could not open {filename}. Make sure you are using a valid file'
        logger.debug(msg)
        raise GeoNodeException(msg)

    base_name, extension = os.path.splitext(filename)
    # Replace special characters in filenames - []{}()
    glob_name = re.sub(r'([\[\]\(\)\{\}])', r'[\g<1>]', base_name)

    if extension.lower() == '.shp':
        required_extensions = dict(
            shp='.[sS][hH][pP]', dbf='.[dD][bB][fF]', shx='.[sS][hH][xX]')
        for ext, pattern in required_extensions.items():
            matches = glob.glob(glob_name + pattern)
            if len(matches) == 0:
                msg = ('Expected helper file %s does not exist; a Shapefile '
                       'requires helper files with the following extensions: '
                       '%s') % (f"{base_name}.{ext}",
                                list(required_extensions.keys()))
                raise GeoNodeException(msg)
            elif len(matches) > 1:
                msg = ('Multiple helper files for %s exist; they need to be '
                       'distinct by spelling and not just case.') % filename
                raise GeoNodeException(msg)
            else:
                files[ext] = matches[0]

        matches = glob.glob(f"{glob_name}.[pP][rR][jJ]")
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
        matches = glob.glob(f"{os.path.dirname(glob_name)}.[sS][lL][dD]")
        if len(matches) == 1:
            files['sld'] = matches[0]
        else:
            matches = glob.glob(f"{glob_name}.[sS][lL][dD]")
            if len(matches) == 1:
                files['sld'] = matches[0]
            elif len(matches) > 1:
                msg = ('Multiple style files (sld) for %s exist; they need to be '
                       'distinct by spelling and not just case.') % filename
                raise GeoNodeException(msg)

    matches = glob.glob(f"{glob_name}.[xX][mM][lL]")

    # shapefile XML metadata is sometimes named base_name.shp.xml
    # try looking for filename.xml if base_name.xml does not exist
    if len(matches) == 0:
        matches = glob.glob(f"{filename}.[xX][mM][lL]")

    if len(matches) == 1:
        files['xml'] = matches[0]
    elif len(matches) > 1:
        msg = ('Multiple XML files for %s exist; they need to be '
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
        zf = ZipFile(filename, allowZip64=True)
        # ZipFile doesn't support with statement in 2.6, so don't do it
        with zf:
            for n in zf.namelist():
                b, e = os.path.splitext(n.lower())
                if e in shp_exts or e in cov_exts or e in csv_exts:
                    extension = e

    if extension.lower() == '.tar' or filename.endswith('.tar.gz'):
        tf = tarfile.open(filename)
        # TarFile doesn't support with statement in 2.6, so don't do it
        with tf:
            for n in tf.getnames():
                b, e = os.path.splitext(n.lower())
                if e in shp_exts or e in cov_exts or e in csv_exts:
                    extension = e

    if extension.lower() in vec_exts:
        return 'vector'
    elif extension.lower() in cov_exts:
        return 'raster'
    else:
        msg = f'Saving of extension [{extension}] is not implemented'
        raise GeoNodeException(msg)


def get_valid_name(layer_name):
    """
    Create a brand new name
    """
    name = _clean_string(layer_name)
    proposed_name = name
    while Layer.objects.filter(name=proposed_name).exists():
        possible_chars = string.ascii_lowercase + string.digits
        suffix = "".join([choice(possible_chars) for i in range(4)])
        proposed_name = f'{name}_{suffix}'
        logger.debug('Requested name already used; adjusting name '
                     '[%s] => [%s]', layer_name, proposed_name)

    return proposed_name


def get_valid_layer_name(layer, overwrite):
    """Checks if the layer is a string and fetches it from the database.
    """
    # The first thing we do is get the layer name string
    if isinstance(layer, Layer):
        layer_name = layer.name
    elif isinstance(layer, str):
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
    try:
        gtif = gdal.Open(filename)
        gt = gtif.GetGeoTransform()
        __, resx, __, __, __, resy = gt
        resolution = f'{resx} {resy}'
        return resolution
    except Exception:
        return None


def get_bbox(filename):
    """Return bbox in the format [xmin,xmax,ymin,ymax]."""
    from django.contrib.gis.gdal import DataSource, SRSException
    srid = 4326
    bbox_x0, bbox_y0, bbox_x1, bbox_y1 = -180, -90, 180, 90

    try:
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
    except Exception:
        pass

    return [bbox_x0, bbox_x1, bbox_y0, bbox_y1, f"EPSG:{str(srid)}"]


@transaction.atomic
def file_upload(filename,
                layer=None,
                gtype=None,
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
    if layer:
        latest_uploads = UploadSession.objects.filter(resource=layer).order_by('-date')
        if latest_uploads.count() > 1:
            upload_session = latest_uploads.first()
        else:
            upload_session, _created = UploadSession.objects.get_or_create(resource=layer)
        upload_session.user = theuser
        upload_session.layerfile_set.all().delete()
    else:
        upload_session = UploadSession.objects.create(user=theuser)

    # Get all the files uploaded with the layer
    if os.path.exists(filename):
        files = get_files(filename)
    else:
        raise Exception(
            _("You are attempting to replace a vector layer with an unknown format."))

    # We are going to replace an existing Layer...
    if layer and overwrite:
        if layer.is_vector() and is_raster(filename):
            raise Exception(_(
                "You are attempting to replace a vector layer with a raster."))
        elif (not layer.is_vector()) and is_vector(filename):
            raise Exception(_(
                "You are attempting to replace a raster layer with a vector."))

        if layer.is_vector():
            absolute_base_file = None
            try:
                if 'shp' in files and os.path.exists(files['shp']):
                    absolute_base_file = _fixup_base_file(files['shp'])
                elif 'zip' in files and os.path.exists(files['zip']):
                    absolute_base_file = _fixup_base_file(files['zip'])
            except Exception:
                absolute_base_file = None

            if not absolute_base_file or \
                    os.path.splitext(absolute_base_file)[1].lower() != '.shp':
                raise Exception(
                    _("You are attempting to replace a vector layer with an unknown format."))
            else:
                try:
                    gtype = layer.gtype if not gtype else gtype
                    inDataSource = ogr.Open(absolute_base_file)
                    lyr = inDataSource.GetLayer(str(layer.name))
                    if not lyr:
                        raise Exception(
                            _("Please ensure the name is consistent with the file you are trying to replace."))
                    schema_is_compliant = False
                    _ff = json.loads(lyr.GetFeature(0).ExportToJson())
                    if gtype:
                        logger.warning(
                            _("Local GeoNode layer has no geometry type."))
                        if _ff["geometry"]["type"] in gtype or gtype in _ff["geometry"]["type"]:
                            schema_is_compliant = True
                    elif "geometry" in _ff and _ff["geometry"]["type"]:
                        schema_is_compliant = True

                    if not schema_is_compliant:
                        raise Exception(
                            _("Please ensure there is at least one geometry type \
                                that is consistent with the file you are trying to replace."))
                except Exception as e:
                    raise Exception(
                        _(f"Some error occurred while trying to access the uploaded schema: {str(e)}"))

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
        except Exception:
            pass

    # Generate a name that is not taken if overwrite is False.
    valid_name = get_valid_layer_name(name, overwrite)

    # Add them to the upload session (new file fields are created).
    assigned_name = None
    for type_name, fn in files.items():
        with open(fn, 'rb') as f:
            upload_session.layerfile_set.create(
                name=type_name, file=File(
                    f, name=f'{assigned_name or valid_name}.{type_name}'))
            # save the system assigned name for the remaining files
            if not assigned_name:
                the_file = upload_session.layerfile_set.all()[0].file.name
                assigned_name = os.path.splitext(os.path.basename(the_file))[0]

    # Get a bounding box
    bbox_x0, bbox_x1, bbox_y0, bbox_y1, srid = get_bbox(filename)

    # by default, if RESOURCE_PUBLISHING=True then layer.is_published
    # must be set to False
    if not overwrite:
        if settings.RESOURCE_PUBLISHING:
            is_published = False
        if settings.ADMIN_MODERATE_UPLOADS:
            is_approved = False

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

        if identifier:
            if ResourceBase.objects.filter(uuid=identifier).count():
                logger.error("The UUID identifier from the XML Metadata is already in use in this system.")
                raise GeoNodeException(
                    _("The UUID identifier from the XML Metadata is already in use in this system."))
            else:
                defaults['uuid'] = identifier

        for key, value in vals.items():
            if key == 'spatial_representation_type':
                value = SpatialRepresentationType(identifier=value)
            elif key == 'topic_category':
                value, created = TopicCategory.objects.get_or_create(
                    identifier=value,
                    defaults={'description': '', 'gn_description': value})
                key = 'category'
            defaults[key] = value

    regions_resolved, regions_unresolved = resolve_regions(regions)
    keywords.extend(regions_unresolved)

    # If it is a vector file, create the layer in postgis.
    if is_vector(filename):
        defaults['storeType'] = 'dataStore'

    # If it is a raster file, get the resolution.
    if is_raster(filename):
        defaults['storeType'] = 'coverageStore'

    # Create a Django object.
    created = False
    layer = None
    try:
        with transaction.atomic():
            if overwrite:
                try:
                    layer = Layer.objects.get(name=valid_name)
                except Layer.DoesNotExist:
                    layer = None
            if not layer:
                if not metadata_upload_form:
                    layer = Layer.objects.filter(name=valid_name, workspace=settings.DEFAULT_WORKSPACE).first()
                    if not layer:
                        layer = Layer.objects.create(
                            name=valid_name,
                            workspace=settings.DEFAULT_WORKSPACE
                        )
                        created = True
                elif identifier:
                    layer = Layer.objects.filter(uuid=identifier).first()
                    if not layer:
                        layer = Layer.objects.create(uuid=identifier)
                        created = True
    except IntegrityError:
        raise

    # Delete the old layers if overwrite is true
    # and the layer was not just created
    # process the layer again after that by
    # doing a layer.save()
    if not created and overwrite:
        # update with new information
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

        if upload_session:
            if layer.upload_session:
                layer.upload_session.date = upload_session.date
                layer.upload_session.user = upload_session.user
                layer.upload_session.error = upload_session.error
                layer.upload_session.traceback = upload_session.traceback
                layer.upload_session.context = upload_session.context
                upload_session = layer.upload_session
            else:
                layer.upload_session = upload_session
    if upload_session:
        defaults['upload_session'] = upload_session
        upload_session.resource = layer
        upload_session.processed = False
        upload_session.save()

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

    if not defaults.get('title', title):
        defaults['title'] = layer.title or layer.name
    if not defaults.get('abstract', abstract):
        defaults['abstract'] = layer.abstract or ''

    to_update = {}
    to_update['upload_session'] = defaults.pop('upload_session', layer.upload_session)
    to_update['storeType'] = defaults.pop('storeType', layer.storeType)
    to_update['charset'] = defaults.pop('charset', layer.charset)
    to_update.update(defaults)
    if defaults.get('date', date) is not None:
        to_update['date'] = defaults.get('date',
                                         datetime.strptime(date, '%Y-%m-%d %H:%M:%S') if date else None)

    # Update ResourceBase
    if not to_update:
        pass
    else:
        try:
            with transaction.atomic():
                if 'spatial_representation_type' in defaults:
                    _spatial_ref_type = defaults.pop('spatial_representation_type')
                    _spatial_ref_type.save()
                    defaults['spatial_representation_type'] = _spatial_ref_type
                ResourceBase.objects.filter(
                    id=layer.resourcebase_ptr.id).update(
                    **defaults)
                Layer.objects.filter(id=layer.id).update(**to_update)

                # Refresh from DB
                layer.refresh_from_db()

                # Pass the parameter overwrite to tell whether the
                # geoserver_post_save_signal should upload the new file or not
                layer.overwrite = overwrite

                # Blank out the store if overwrite is true.
                # geoserver_post_save_signal should upload the new file if needed
                layer.store = '' if overwrite else layer.store
        except IntegrityError:
            raise
    try:
        with transaction.atomic():
            layer.save(notify=True)
    except IntegrityError:
        raise
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
        print("Verifying that GeoNode is running ...", file=console)

    if console is None:
        console = open(os.devnull, 'w')

    potential_files = []
    if os.path.isfile(incoming):
        ___, short_filename = os.path.split(incoming)
        basename, extension = os.path.splitext(short_filename)
        filename = incoming

        if extension in {'.tif', '.shp', '.tar', '.zip'}:
            potential_files.append((basename, filename))
        elif short_filename.endswith('.tar.gz'):
            potential_files.append((basename, filename))

    elif not os.path.isdir(incoming):
        msg = f'Please pass a filename or a directory name as the "incoming" parameter, instead of {incoming}: {type(incoming)}'
        logger.exception(msg)
        raise GeoNodeException(msg)
    else:
        datadir = incoming
        for root, dirs, files in os.walk(datadir):
            for short_filename in files:
                basename, extension = os.path.splitext(short_filename)
                filename = os.path.join(root, short_filename)
                if extension in {'.tif', '.shp', '.tar', '.zip'}:
                    potential_files.append((basename, filename))
                elif short_filename.endswith('.tar.gz'):
                    potential_files.append((basename, filename))

    # After gathering the list of potential files,
    # let's process them one by one.
    number = len(potential_files)
    if verbosity > 1:
        msg = "Found %d potential layers." % number
        print(msg, file=console)

    if (number > 1) and (name is not None):
        msg = 'Failed to process.  Cannot specify name with multiple imports.'
        raise Exception(msg)

    output = []
    for i, file_pair in enumerate(potential_files):
        basename, filename = file_pair
        existing_layers = Layer.objects.filter(name=basename)

        existed = existing_layers.count() > 0

        if existed and skip:
            save_it = False
            status = 'skipped'
            layer = existing_layers[0]
            if verbosity > 0:
                msg = ('Stopping process because '
                       '--overwrite was not set '
                       'and a layer with this name already exists.')
                print(msg, file=sys.stderr)
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
            except Exception as e:
                if ignore_errors:
                    status = 'failed'
                    exception_type, error, traceback = sys.exc_info()
                else:
                    if verbosity > 0:
                        msg = ('Stopping process because '
                               '--ignore-errors was not set '
                               'and an error was found.')
                        print(msg, file=sys.stderr)
                        raise Exception from e

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
            print(msg, file=console)
    return output


def delete_orphaned_layers():
    """Delete orphaned layer files."""
    deleted = []
    _, files = storage.listdir("layers")

    for filename in files:
        if LayerFile.objects.filter(file__icontains=filename).count() == 0:
            logger.debug(f"Deleting orphaned layer file {filename}")
            try:
                storage.delete(os.path.join("layers", filename))
                deleted.append(filename)
            except NotImplementedError as e:
                logger.error(
                    f"Failed to delete orphaned layer file '{filename}': {e}")

    return deleted


def surrogate_escape_string(input_string, source_character_set):
    """
    Escapes a given input string using the provided source character set,
    using the `surrogateescape` codec error handler.
    """

    return input_string.encode(source_character_set, "surrogateescape").decode("utf-8", "surrogateescape")


def set_layers_permissions(permissions_name, resources_names=None,
                           users_usernames=None, groups_names=None,
                           delete_flag=None, verbose=False):
    # Processing information
    if not resources_names:
        # If resources is None we consider all the existing layer
        resources = Layer.objects.all()
    else:
        try:
            resources = Layer.objects.filter(Q(title__in=resources_names) | Q(name__in=resources_names))
        except Layer.DoesNotExist:
            logger.warning(
                f"No resources have been found with these names: {', '.join(resources_names)}."
            )
    if not resources:
        logger.warning("No resources have been found. No update operations have been executed.")
    else:
        # PERMISSIONS
        if not permissions_name:
            logger.error("No permissions have been provided.")
        else:
            permissions = []
            if permissions_name.lower() in ('read', 'r'):
                if not delete_flag:
                    permissions = READ_PERMISSIONS
                else:
                    permissions = READ_PERMISSIONS + WRITE_PERMISSIONS \
                        + DOWNLOAD_PERMISSIONS + OWNER_PERMISSIONS
            elif permissions_name.lower() in ('write', 'w'):
                if not delete_flag:
                    permissions = READ_PERMISSIONS + WRITE_PERMISSIONS
                else:
                    permissions = WRITE_PERMISSIONS
            elif permissions_name.lower() in ('download', 'd'):
                if not delete_flag:
                    permissions = READ_PERMISSIONS + DOWNLOAD_PERMISSIONS
                else:
                    permissions = DOWNLOAD_PERMISSIONS
            elif permissions_name.lower() in ('owner', 'o'):
                if not delete_flag:
                    permissions = READ_PERMISSIONS + WRITE_PERMISSIONS \
                        + DOWNLOAD_PERMISSIONS + OWNER_PERMISSIONS
                else:
                    permissions = OWNER_PERMISSIONS
            if not permissions:
                logger.error(
                    "Permission must match one of these values: read (r), write (w), download (d), owner (o)."
                )
            else:
                if not users_usernames and not groups_names:
                    logger.error(
                        "At least one user or one group must be provided."
                    )
                else:
                    # USERS
                    users = []
                    if users_usernames:
                        User = get_user_model()
                        for username in users_usernames:
                            try:
                                user = User.objects.get(username=username)
                                users.append(user)
                            except User.DoesNotExist:
                                logger.warning(
                                    f'The user {username} does not exists. It has been skipped.'
                                )
                    # GROUPS
                    groups = []
                    if groups_names:
                        for group_name in groups_names:
                            try:
                                group = Group.objects.get(name=group_name)
                                groups.append(group)
                            except Group.DoesNotExist:
                                logger.warning(
                                    f'The group {group_name} does not exists. It has been skipped.'
                                )
                    if not users and not groups:
                        logger.error(
                            'Neither users nor groups corresponding to the typed names have been found. '
                            'No update operations have been executed.'
                        )
                    else:
                        # RESOURCES
                        for resource in resources:
                            # Existing permissions on the resource
                            perm_spec = resource.get_all_level_info()
                            if verbose:
                                logger.info(
                                    f"Initial permissions info for the resource {resource.title}: {perm_spec}"
                                )
                                print(
                                    f"Initial permissions info for the resource {resource.title}: {perm_spec}"
                                )
                            for u in users:
                                _user = u
                                # Add permissions
                                if not delete_flag:
                                    # Check the permission already exists
                                    if _user not in perm_spec["users"] and _user.username not in perm_spec["users"]:
                                        perm_spec["users"][_user] = permissions
                                    else:
                                        if _user.username in perm_spec["users"]:
                                            u_perms_list = perm_spec["users"][_user.username]
                                            del(perm_spec["users"][_user.username])
                                            perm_spec["users"][_user] = u_perms_list

                                        try:
                                            u_perms_list = perm_spec["users"][_user]
                                            base_set = set(u_perms_list)
                                            target_set = set(permissions)
                                            perm_spec["users"][_user] = list(base_set | target_set)
                                        except KeyError:
                                            perm_spec["users"][_user] = permissions

                                # Delete permissions
                                else:
                                    # Skip resource owner
                                    if _user != resource.owner:
                                        if _user in perm_spec["users"]:
                                            u_perms_set = set()
                                            for up in perm_spec["users"][_user]:
                                                if up not in permissions:
                                                    u_perms_set.add(up)
                                            perm_spec["users"][_user] = list(u_perms_set)
                                        else:
                                            logger.warning(
                                                f"The user {_user.username} does not have any permission on the layer {resource.title}. It has been skipped."
                                            )
                                    else:
                                        logger.warning(
                                            f"Warning! - The user {_user.username} is the layer {resource.title} owner, so its permissions can't be changed. It has been skipped."
                                        )
                            for g in groups:
                                _group = g
                                # Add permissions
                                if not delete_flag:
                                    # Check the permission already exists
                                    if _group not in perm_spec["groups"] and _group.name not in perm_spec["groups"]:
                                        perm_spec["groups"][_group] = permissions
                                    else:
                                        if _group.name in perm_spec["groups"]:
                                            g_perms_list = perm_spec["groups"][_group.name]
                                            del(perm_spec["groups"][_group.name])
                                            perm_spec["groups"][_group] = g_perms_list

                                        try:
                                            g_perms_list = perm_spec["groups"][_group]
                                            base_set = set(g_perms_list)
                                            target_set = set(permissions)
                                            perm_spec["groups"][_group] = list(base_set | target_set)
                                        except KeyError:
                                            perm_spec["groups"][_group] = permissions

                                # Delete permissions
                                else:
                                    if g in perm_spec["groups"]:
                                        g_perms_set = set()
                                        for gp in perm_spec["groups"][g]:
                                            if gp not in permissions:
                                                g_perms_set.add(gp)
                                        perm_spec["groups"][g] = list(g_perms_set)
                                    else:
                                        logger.warning(
                                            f"The group {g.name} does not have any permission on the layer {resource.title}. It has been skipped."
                                        )
                            # Set final permissions
                            resource.set_permissions(perm_spec)
                            if verbose:
                                logger.info(
                                    f"Final permissions info for the resource {resource.title}: {perm_spec}"
                                )
                                print(
                                    f"Final permissions info for the resource {resource.title}: {perm_spec}"
                                )
                        if verbose:
                            logger.info("Permissions successfully updated!")
                            print("Permissions successfully updated!")


def get_uuid_handler():
    from django.utils.module_loading import import_string
    return import_string(settings.LAYER_UUID_HANDLER)
