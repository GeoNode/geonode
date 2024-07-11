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
import copy
import re
import os
import glob
import string
import logging
import tarfile

from osgeo import gdal, osr
from zipfile import ZipFile, is_zipfile
from random import choice

# Django functionality
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.utils.module_loading import import_string
from django.core.exceptions import ObjectDoesNotExist

from geonode.security.permissions import PermSpec, PermSpecCompact
from geonode.storage.manager import storage_manager

# Geonode functionality
from geonode.base.models import Region
from geonode.utils import check_ogc_backend
from geonode import GeoNodeException, geoserver
from geonode.layers.models import shp_exts, csv_exts, vec_exts, cov_exts, Dataset

READ_PERMISSIONS = ["view_resourcebase"]
WRITE_PERMISSIONS = ["change_dataset_data", "change_dataset_style", "change_resourcebase_metadata"]
DOWNLOAD_PERMISSIONS = ["download_resourcebase"]
OWNER_PERMISSIONS = [
    "change_resourcebase",
    "delete_resourcebase",
    "change_resourcebase_permissions",
    "publish_resourcebase",
]

logger = logging.getLogger("geonode.layers.utils")

_separator = f"\n{'-' * 100}\n"


def _clean_string(str, regex=r"(^[^a-zA-Z\._]+)|([^a-zA-Z\._0-9]+)", replace="_"):
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
                    region_resolved = Region.objects.get(Q(name__iexact=region) | Q(code__iexact=region))
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
        filename.encode("ascii")
    except UnicodeEncodeError:
        msg = f"Please use only characters from the english alphabet for the filename. '{os.path.basename(filename).encode('UTF-8', 'strict')}' is not yet supported."
        raise GeoNodeException(msg)

    # Let's unzip the filname in case it is a ZIP file
    from geonode.utils import unzip_file, mkdtemp

    tempdir = None
    if is_zipfile(filename):
        tempdir = mkdtemp()
        _filename = unzip_file(filename, ".shp", tempdir=tempdir)
        if not _filename:
            # We need to iterate files as filename could be the zipfile
            import ntpath
            from geonode.upload.utils import _SUPPORTED_EXT

            file_basename, file_ext = ntpath.splitext(filename)
            for item in os.listdir(tempdir):
                item_basename, item_ext = ntpath.splitext(item)
                if ntpath.basename(item_basename) == ntpath.basename(file_basename) and (
                    item_ext.lower() in _SUPPORTED_EXT
                ):
                    filename = os.path.join(tempdir, item)
                    break
        else:
            filename = _filename

    # Make sure the file exists.
    if not os.path.exists(filename):
        msg = f"Could not open {filename}. Make sure you are using a valid file"
        logger.debug(msg)
        raise GeoNodeException(msg)

    base_name, extension = os.path.splitext(filename)
    # Replace special characters in filenames - []{}()
    glob_name = re.sub(r"([\[\]\(\)\{\}])", r"[\g<1>]", base_name)

    if extension.lower() == ".shp":
        required_extensions = dict(shp=".[sS][hH][pP]", dbf=".[dD][bB][fF]", shx=".[sS][hH][xX]")
        for ext, pattern in required_extensions.items():
            matches = glob.glob(glob_name + pattern)
            if len(matches) == 0:
                msg = (
                    f"Expected helper file {base_name}.{ext} does not exist; a Shapefile "
                    "requires helper files with the following extensions: "
                    f"{list(required_extensions.keys())}"
                )
                raise GeoNodeException(msg)
            elif len(matches) > 1:
                msg = (
                    "Multiple helper files for %s exist; they need to be " "distinct by spelling and not just case."
                ) % filename
                raise GeoNodeException(msg)
            else:
                files[ext] = matches[0]

        matches = glob.glob(f"{glob_name}.[pP][rR][jJ]")
        if len(matches) == 1:
            files["prj"] = matches[0]
        elif len(matches) > 1:
            msg = (
                "Multiple helper files for %s exist; they need to be " "distinct by spelling and not just case."
            ) % filename
            raise GeoNodeException(msg)

    elif extension.lower() in cov_exts:
        files[extension.lower().replace(".", "")] = filename

    # Only for GeoServer
    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        matches = glob.glob(f"{os.path.dirname(glob_name)}.[sS][lL][dD]")
        if len(matches) == 1:
            files["sld"] = matches[0]
        else:
            matches = glob.glob(f"{glob_name}.[sS][lL][dD]")
            if len(matches) == 1:
                files["sld"] = matches[0]
            elif len(matches) > 1:
                msg = (
                    "Multiple style files (sld) for %s exist; they need to be "
                    "distinct by spelling and not just case."
                ) % filename
                raise GeoNodeException(msg)

    matches = glob.glob(f"{glob_name}.[xX][mM][lL]")

    # shapefile XML metadata is sometimes named base_name.shp.xml
    # try looking for filename.xml if base_name.xml does not exist
    if len(matches) == 0:
        matches = glob.glob(f"{filename}.[xX][mM][lL]")

    if len(matches) == 1:
        files["xml"] = matches[0]
    elif len(matches) > 1:
        msg = ("Multiple XML files for %s exist; they need to be " "distinct by spelling and not just case.") % filename
        raise GeoNodeException(msg)

    return files, tempdir


def dataset_type(filename):
    """Finds out if a filename is a Feature or a Vector
    returns a gsconfig resource_type string
    that can be either 'featureType' or 'coverage'
    """
    base_name, extension = os.path.splitext(filename)

    if extension.lower() == ".zip":
        zf = ZipFile(filename, allowZip64=True)
        # ZipFile doesn't support with statement in 2.6, so don't do it
        with zf:
            for n in zf.namelist():
                b, e = os.path.splitext(n.lower())
                if e in shp_exts or e in cov_exts or e in csv_exts:
                    extension = e

    if extension.lower() == ".tar" or filename.endswith(".tar.gz"):
        tf = tarfile.open(filename)
        # TarFile doesn't support with statement in 2.6, so don't do it
        with tf:
            for n in tf.getnames():
                b, e = os.path.splitext(n.lower())
                if e in shp_exts or e in cov_exts or e in csv_exts:
                    extension = e

    if extension.lower() in vec_exts:
        return "vector"
    elif extension.lower() in cov_exts:
        return "raster"
    else:
        msg = f"Saving of extension [{extension}] is not implemented"
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
        proposed_name = f"{name}_{suffix}"
        logger.debug("Requested name already used; adjusting name " f"[{dataset_name}] => [{proposed_name}]")

    return proposed_name


def get_valid_dataset_name(layer, overwrite):
    """Checks if the layer is a string and fetches it from the database."""
    # The first thing we do is get the layer name string
    if isinstance(layer, Dataset):
        dataset_name = layer.name
    elif isinstance(layer, str):
        dataset_name = str(layer)
    else:
        msg = "You must pass either a filename or a GeoNode dataset object"
        raise GeoNodeException(msg)

    if overwrite:
        return dataset_name
    else:
        return get_valid_name(dataset_name)


def get_default_user():
    """Create a default user"""
    superusers = get_user_model().objects.filter(is_superuser=True).order_by("id")
    if superusers.exists():
        # Return the first created superuser
        return superusers[0]
    else:
        raise GeoNodeException(
            "You must have an admin account configured "
            "before importing data. "
            "Try: django-admin.py createsuperuser"
        )


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
        resolution = f"{resx} {resy}"
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
                    raise GeoNodeException("Invalid Projection. Dataset is missing CRS!")
                srs.identify_epsg()
            except SRSException:
                pass
            epsg_code = srs.srid
            # can't find epsg code, then check if bbox is within the 4326 boundary
            if epsg_code is None and (
                x_min <= bbox_x0 <= x_max
                and x_min <= bbox_x1 <= x_max
                and y_min <= bbox_y0 <= y_max
                and y_min <= bbox_y1 <= y_max
            ):
                # set default epsg code
                epsg_code = "4326"
            elif epsg_code is None:
                # otherwise, stop the upload process
                raise GeoNodeException("Invalid    Datasets. " "Needs an authoritative SRID in its CRS to be accepted")

            # eliminate default EPSG srid as it will be added when this function returned
            srid = epsg_code if epsg_code else "4326"
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
            srid = srs.GetAuthorityCode(None) if srs else "4326"
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
                logger.error(f"Failed to delete orphaned dataset file '{filename}': {e}")

    return deleted


def surrogate_escape_string(input_string, source_character_set):
    """
    Escapes a given input string using the provided source character set,
    using the `surrogateescape` codec error handler.
    """

    return input_string.encode(source_character_set, "surrogateescape").decode("utf-8", "surrogateescape")


def set_datasets_permissions(
    permissions_name, resources_names=None, users_usernames=None, groups_names=None, delete_flag=False, verbose=False
):
    # here to avoid circular import
    from geonode.resource.manager import resource_manager

    # Processing information
    resources_as_pk = []
    for el in resources_names or []:
        if isinstance(el, str) and not el.isnumeric():
            res = Dataset.objects.filter(Q(title=el) | Q(name=el))
            if res.exists():
                resources_as_pk.append(res.first().pk)
        else:
            resources_as_pk.append(el)

    not_found = []
    final_perms_payload = {}

    for rpk in resources_as_pk:
        resource = Dataset.objects.filter(pk=rpk)
        if not resource.exists():
            not_found.append(rpk)
            logger.error(f"Resource named: {rpk} not found, skipping....")
            continue
        else:
            # creating the payload from the CompactPermissions like we do in the UI.
            # the result will be a payload with the compact permissions list required
            # for the selected resource
            resource = resource.first()
            # getting the actual permissions available for the dataset
            original_perms = PermSpec(resource.get_all_level_info(), resource)
            new_perms_payload = {"organizations": [], "users": [], "groups": []}
            # if the username is specified, we add them to the payload with the compact
            # perm value
            if users_usernames:
                User = get_user_model()
                for _user in users_usernames:
                    try:
                        new_perms_payload["users"].append(
                            {"id": User.objects.get(username=_user).pk, "permissions": permissions_name}
                        )
                    except User.DoesNotExist:
                        logger.warning(f"The user {_user} does not exists. " "It has been skipped.")
            # GROUPS
            # if the group is specified, we add them to the payload with the compact
            # perm value
            if groups_names:
                for group_name in groups_names:
                    try:
                        new_perms_payload["groups"].append(
                            {"id": Group.objects.get(name=group_name).pk, "permissions": permissions_name}
                        )
                    except Group.DoesNotExist:
                        logger.warning(f"The group {group_name} does not exists. " "It has been skipped.")
            # Using the compact permissions payload to calculate the permissions
            # that we want to give for each user/group
            # This part is in common with the permissions API
            new_compact_perms = PermSpecCompact(new_perms_payload, resource)
            copy_compact_perms = copy.deepcopy(new_compact_perms)

            perms_spec_compact_resource = PermSpecCompact(original_perms.compact, resource)
            perms_spec_compact_resource.merge(new_compact_perms)

            final_perms_payload = perms_spec_compact_resource.extended
            # if the delete flag is set, we must delete the permissions for the input user/group
            if delete_flag:
                # since is a delete operation, we must remove the users/group from the resource
                # so this will return the updated dict without the user/groups to be removed
                final_perms_payload["users"] = {
                    _user: _perms
                    for _user, _perms in perms_spec_compact_resource.extended["users"].items()
                    if _user not in copy_compact_perms.extended["users"]
                }
                final_perms_payload["groups"] = {
                    _group: _perms
                    for _group, _perms in perms_spec_compact_resource.extended["groups"].items()
                    if _group not in copy_compact_perms.extended["groups"]
                }
                if final_perms_payload["users"].get("AnonymousUser") is None and final_perms_payload["groups"].get(
                    "anonymous"
                ):
                    final_perms_payload["groups"].pop("anonymous")

            # calling the resource manager to set the permissions
            resource_manager.set_permissions(resource.uuid, instance=resource, permissions=final_perms_payload)


def get_uuid_handler():
    return import_string(settings.LAYER_UUID_HANDLER)


default_dataset_download_handler = None
dataset_download_handler_list = []


def get_download_handlers():
    if not dataset_download_handler_list and getattr(settings, "DATASET_DOWNLOAD_HANDLERS", None):
        dataset_download_handler_list.append(import_string(settings.DATASET_DOWNLOAD_HANDLERS[0]))

    return dataset_download_handler_list


def get_default_dataset_download_handler():
    global default_dataset_download_handler
    if not default_dataset_download_handler and getattr(settings, "DEFAULT_DATASET_DOWNLOAD_HANDLER", None):
        default_dataset_download_handler = import_string(settings.DEFAULT_DATASET_DOWNLOAD_HANDLER)

    return default_dataset_download_handler


def set_default_dataset_download_handler(handler):
    global default_dataset_download_handler
    handler_module = import_string(handler)
    if handler_module not in dataset_download_handler_list:
        dataset_download_handler_list.append(handler_module)

    default_dataset_download_handler = handler_module


def clear_dataset_download_handlers():
    global default_dataset_download_handler
    dataset_download_handler_list.clear()
    default_dataset_download_handler = None
