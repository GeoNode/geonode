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
import json
import string
import logging
import tarfile

from osgeo import gdal, osr, ogr
from zipfile import ZipFile, is_zipfile
from random import choice

# Django functionality
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from django.core.exceptions import ObjectDoesNotExist, SuspiciousFileOperation
from geonode.layers.api.exceptions import InvalidDatasetException
from geonode.storage.manager import storage_manager
# Geonode functionality
from geonode.base.models import Region
from geonode.utils import check_ogc_backend
from geonode import GeoNodeException, geoserver
from geonode.geoserver.helpers import gs_catalog
from geonode.layers.models import shp_exts, csv_exts, vec_exts, cov_exts, Dataset

READ_PERMISSIONS = [
    'view_resourcebase'
]
WRITE_PERMISSIONS = [
    'change_dataset_data',
    'change_dataset_style',
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
    if regions and len(regions) > 0:
        for region in regions:
            try:
                if region.isnumeric():
                    region_resolved = Region.objects.get(id=int(region))
                else:
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
    from geonode.utils import unzip_file, mkdtemp
    tempdir = None
    if is_zipfile(filename):
        tempdir = mkdtemp()
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
                msg = (f'Expected helper file {base_name}.{ext} does not exist; a Shapefile '
                       'requires helper files with the following extensions: '
                       f'{list(required_extensions.keys())}')
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

    return files, tempdir


def dataset_type(filename):
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


def get_valid_name(dataset_name):
    """
    Create a brand new name
    """
    name = _clean_string(dataset_name)
    proposed_name = name
    while Dataset.objects.filter(name=proposed_name).exists():
        possible_chars = string.ascii_lowercase + string.digits
        suffix = "".join([choice(possible_chars) for i in range(4)])
        proposed_name = f'{name}_{suffix}'
        logger.debug('Requested name already used; adjusting name '
                     f'[{dataset_name}] => [{proposed_name}]')

    return proposed_name


def get_valid_dataset_name(layer, overwrite):
    """Checks if the layer is a string and fetches it from the database.
    """
    # The first thing we do is get the layer name string
    if isinstance(layer, Dataset):
        dataset_name = layer.name
    elif isinstance(layer, str):
        dataset_name = str(layer)
    else:
        msg = ('You must pass either a filename or a GeoNode dataset object')
        raise GeoNodeException(msg)

    if overwrite:
        return dataset_name
    else:
        return get_valid_name(dataset_name)


def get_default_user():
    """Create a default user
    """
    superusers = get_user_model().objects.filter(
        is_superuser=True).order_by('id')
    if superusers.exists():
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
                    raise GeoNodeException('Invalid Projection. Dataset is missing CRS!')
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
                    "Invalid    Datasets. "
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


def delete_orphaned_datasets():
    """Delete orphaned layer files."""
    deleted = []
    _, files = storage_manager.listdir("layers")

    for filename in files:
        if Dataset.objects.filter(file__icontains=filename).count() == 0:
            logger.debug(f"Deleting orphaned dataset file {filename}")
            try:
                storage_manager.delete(os.path.join("layers", filename))
                deleted.append(filename)
            except NotImplementedError as e:
                logger.error(
                    f"Failed to delete orphaned dataset file '{filename}': {e}")

    return deleted


def surrogate_escape_string(input_string, source_character_set):
    """
    Escapes a given input string using the provided source character set,
    using the `surrogateescape` codec error handler.
    """

    return input_string.encode(source_character_set, "surrogateescape").decode("utf-8", "surrogateescape")


def set_datasets_permissions(permissions_name, resources_names=None, users_usernames=None, groups_names=None, delete_flag=False, verbose=False):
    # Processing information
    if not resources_names:
        # If resources is None we consider all the existing layer
        resources = Dataset.objects.all()
    else:
        try:
            resources = Dataset.objects.filter(Q(title__in=resources_names) | Q(name__in=resources_names))
        except Dataset.DoesNotExist:
            logger.warning(
                f'No resources have been found with these names: {", ".join(resources_names)}.'
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
                        for _user in users_usernames:
                            try:
                                if isinstance(_user, str):
                                    user = User.objects.get(username=_user)
                                else:
                                    user = User.objects.get(username=_user.username)
                                users.append(user)
                            except User.DoesNotExist:
                                logger.warning(
                                    f'The user {_user} does not exists. '
                                    'It has been skipped.'
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
                                    f'The group {group_name} does not exists. '
                                    'It has been skipped.'
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
                                            del (perm_spec["users"][_user.username])
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
                                                f"The user {_user.username} does not have "
                                                f"any permission on the dataset {resource.title}. "
                                                "It has been skipped."
                                            )
                                    else:
                                        logger.warning(
                                            f"Warning! - The user {_user.username} is the "
                                            f"layer {resource.title} owner, "
                                            "so its permissions can't be changed. "
                                            "It has been skipped."
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
                                            del (perm_spec["groups"][_group.name])
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
                                            f"The group {g.name} does not have any permission "
                                            f"on the dataset {resource.title}. "
                                            "It has been skipped."
                                        )
                            # Set final permissions
                            from geonode.resource.manager import resource_manager
                            resource_manager.set_permissions(resource.uuid, instance=resource, permissions=perm_spec)

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


def validate_input_source(layer, filename, files, gtype=None, action_type='replace', storage_manager=storage_manager):
    if layer.is_vector() and is_raster(filename):
        raise InvalidDatasetException(_(
            f"You are attempting to {action_type} a vector dataset with a raster."))
    elif (not layer.is_vector()) and is_vector(filename):
        raise InvalidDatasetException(_(
            f"You are attempting to {action_type} a raster dataset with a vector."))

    if layer.is_vector():
        absolute_base_file = None
        try:
            absolute_base_file = storage_manager.path(files['shp'])
        except SuspiciousFileOperation:
            absolute_base_file = files['shp']
        except InvalidDatasetException:
            absolute_base_file = None

        if not absolute_base_file or \
                os.path.splitext(absolute_base_file)[1].lower() != '.shp':
            raise InvalidDatasetException(
                _(f"You are attempting to {action_type} a vector dataset with an unknown format."))
        else:
            try:
                gtype = layer.gtype if not gtype else gtype
                inDataSource = ogr.Open(absolute_base_file)
                if inDataSource is None:
                    raise InvalidDatasetException(
                        _(f"Please ensure that the base_file {absolute_base_file} is not empty"))
                lyr = inDataSource.GetLayer(str(layer.name))
                if not lyr:
                    raise InvalidDatasetException(
                        _(f"Please ensure the name is consistent with the file you are trying to {action_type}."))
                schema_is_compliant = False
                _ff = json.loads(lyr.GetFeature(0).ExportToJson())
                if gtype:
                    logger.warning(
                        _("Local GeoNode dataset has no geometry type."))
                    if _ff["geometry"]["type"] in gtype or gtype in _ff["geometry"]["type"]:
                        schema_is_compliant = True
                elif "geometry" in _ff and _ff["geometry"]["type"]:
                    schema_is_compliant = True

                if not schema_is_compliant:
                    raise InvalidDatasetException(
                        _(f"Please ensure there is at least one geometry type \
                            that is consistent with the file you are trying to {action_type}."))

                new_schema_fields = [field.name for field in lyr.schema]
                gs_dataset = gs_catalog.get_layer(layer.name)

                if not gs_dataset:
                    raise InvalidDatasetException(
                        _("The selected Dataset does not exists in the catalog."))

                gs_dataset = gs_dataset.resource.attributes
                schema_is_compliant = all([x.replace("-", '_') in gs_dataset for x in new_schema_fields])

                if not schema_is_compliant:
                    raise InvalidDatasetException(
                        _("Please ensure that the dataset structure is consistent "
                          f"with the file you are trying to {action_type}."))
                return True
            except Exception as e:
                raise InvalidDatasetException(
                    _(f"Some error occurred while trying to access the uploaded schema: {str(e)}"))


def is_xml_upload_only(request):
    # will check if only the XML file is provided
    return mdata_search_by_type(request, 'xml')


def is_sld_upload_only(request):
    return mdata_search_by_type(request, 'sld')


def mdata_search_by_type(request, filetype):
    files = list({v.name for k, v in request.FILES.items()})
    return len(files) == 1 and all([filetype in f for f in files])
