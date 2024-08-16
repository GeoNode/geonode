#########################################################################
#
# Copyright (C) 2018 OSGeo
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

"""Tools for performing validation of uploaded spatial files."""
import re
import os.path
import logging
import zipfile

from collections import namedtuple

from django import forms
from django.utils.translation import gettext_lazy as _

from . import files
from .utils import get_kml_doc

logger = logging.getLogger(__name__)

ShapefileAux = namedtuple("ShapefileAux", ["extension", "mandatory"])


def _supported_type(ext, supported_types):
    return any([type_.matches(ext) for type_ in supported_types])


def _validate_shapefile_components(possible_filenames):
    """Validates that a shapefile can be loaded from the input file paths

    :arg possible_files: Remaining form upload contents
    :type possible_files: list
    :raises: forms.ValidationError

    """

    shp_files = [str(f) for f in possible_filenames if str(f).lower().endswith(".shp")]
    aux_mandatory = True
    if len(shp_files) > 1:
        raise forms.ValidationError(_("Only one shapefile per zip is allowed"))
    elif len(shp_files) == 0:
        shp_files = [
            f for f in possible_filenames if os.path.splitext(f.lower())[1] in (".shp", ".dbf", ".shx", ".prj")
        ]
        aux_mandatory = False
    try:
        shape_component = shp_files[0]
    except IndexError:
        return None
    base_name, base_extension = os.path.splitext(os.path.basename(shape_component))
    components = [base_extension[1:]]
    shapefile_additional = [
        ShapefileAux(extension="dbf", mandatory=aux_mandatory),
        ShapefileAux(extension="shx", mandatory=aux_mandatory),
        ShapefileAux(extension="prj", mandatory=False),
        ShapefileAux(extension="xml", mandatory=False),
        ShapefileAux(extension="sld", mandatory=False),
    ]
    for additional_component in shapefile_additional:
        for path in possible_filenames:
            additional_name = os.path.splitext(os.path.basename(path))[0]
            matches_main_name = bool(re.match(base_name, additional_name, re.I))
            extension = os.path.splitext(path)[1][1:].lower()
            found_component = extension == additional_component.extension
            if found_component and matches_main_name:
                components.append(additional_component.extension)
                break
        else:
            if additional_component.mandatory:
                raise forms.ValidationError(
                    f"Could not find {additional_component.extension} file, which is mandatory for " "shapefile uploads"
                )
    logger.debug(f"shapefile components: {components}")
    return components


def _validate_kml_bytes(kml_bytes, other_files):
    result = None
    kml_doc, namespaces = get_kml_doc(kml_bytes)
    ground_overlays = kml_doc.xpath("//kml:GroundOverlay", namespaces=namespaces)
    if len(ground_overlays) > 1:
        raise forms.ValidationError(_("kml files with more than one GroundOverlay are not supported"))
    elif len(ground_overlays) == 1:
        try:
            image_path = ground_overlays[0].xpath("kml:Icon/kml:href/text()", namespaces=namespaces)[0].strip()
        except IndexError:
            image_path = ""
        logger.debug(f"image_path: {image_path}")
        logger.debug(f"other_files: {other_files}")
        if image_path not in other_files:
            raise forms.ValidationError(_("Ground overlay image declared in kml file cannot be found"))
        result = ("kml", "sld", os.path.splitext(image_path)[-1][1:])
    return result


def validate_kml(possible_files):
    """Validate uploaded KML file and a possible image companion file

    KML files that specify vectorial data typers are uploaded standalone.
    However, if the KML specifies a GroundOverlay type (raster) they are
    uploaded together with a raster file.

    """
    kml_file = [f for f in possible_files if f.name.lower().endswith(".kml")][0]
    others = [f.name for f in possible_files if not f.name.lower().endswith(".kml")]

    kml_file.seek(0)
    kml_bytes = kml_file.read()
    result = _validate_kml_bytes(kml_bytes, others)
    if not result:
        kml_doc, namespaces = get_kml_doc(kml_bytes)
        if kml_doc and namespaces:
            return (
                "kml",
                "sld",
            )
    return result


def validate_kml_zip(kmz_django_file):
    kml_bytes = None
    with zipfile.ZipFile(kmz_django_file, allowZip64=True) as zip_handler:
        zip_contents = zip_handler.namelist()
        kml_files = [i for i in zip_contents if i.lower().endswith(".kml")]
        if not kml_files:
            return None
        if len(kml_files) > 1:
            raise forms.ValidationError(_("Only one kml file per ZIP is allowed"))
        kml_zip_path = kml_files[0]
        kml_bytes = zip_handler.read(kml_zip_path)
    kml_doc, namespaces = get_kml_doc(kml_bytes)
    if kml_doc and namespaces:
        return ("zip",)
    return None


def validate_kmz(kmz_django_file):
    with zipfile.ZipFile(kmz_django_file, allowZip64=True) as zip_handler:
        zip_contents = zip_handler.namelist()
        kml_files = [i for i in zip_contents if i.lower().endswith(".kml")]
        if len(kml_files) > 1:
            raise forms.ValidationError(_("Only one kml file per kmz is allowed"))
        try:
            kml_zip_path = kml_files[0]
            kml_bytes = zip_handler.read(kml_zip_path)
        except IndexError:
            return None
    other_filenames = [i for i in zip_contents if not i.lower().endswith(".kml")]
    if _validate_kml_bytes(kml_bytes, other_filenames):
        return ("kmz",)
    else:
        return None


def validate_shapefile(zip_django_file):
    valid_extensions = None
    with zipfile.ZipFile(zip_django_file, allowZip64=True) as zip_handler:
        contents = zip_handler.namelist()
        if _validate_shapefile_components(contents):
            valid_extensions = ("zip",)
    return valid_extensions


def validate_raster(contents, allow_multiple=False):
    def dupes(_a):
        return {x for x in _a if _a.count(x) > 1}

    valid_extensions = None
    raster_types = [t for t in files.types if t.dataset_type == files.raster]
    raster_exts = [f".{t.code}" for t in raster_types]
    raster_aliases = []
    for alias in [aliases for aliases in [t.aliases for t in raster_types] if aliases]:
        raster_aliases.extend([f".{a}" for a in alias])
    raster_exts.extend(raster_aliases)

    raster_files = [f for f in contents if os.path.splitext(str(f).lower())[1] in raster_exts]
    other_files = [f for f in contents if os.path.splitext(str(f).lower())[1] not in raster_exts]

    all_extensions = [os.path.splitext(str(f))[1][1:] for f in raster_files]
    other_extensions = tuple({os.path.splitext(str(f))[1][1:] for f in other_files})
    valid_extensions = tuple(set(all_extensions))
    dup_extensions = tuple(dupes(all_extensions))
    if dup_extensions:
        geotiff_extensions = [x for x in dup_extensions if x in files._tif_extensions]
        mosaics_extensions = [x for x in other_extensions if x in files._mosaics_extensions]
        if mosaics_extensions:
            return ("zip-mosaic",)
        elif geotiff_extensions:
            if not allow_multiple:
                raise forms.ValidationError(
                    _("You are trying to upload multiple GeoTIFFs without a valid 'indexer.properties' file.")
                )
            else:
                return ("zip-mosaic",)
        else:
            raise forms.ValidationError(_("Only one raster file per ZIP is allowed"))
    else:
        if valid_extensions:
            if len(valid_extensions) > 1 and not allow_multiple:
                raise forms.ValidationError(_("No multiple rasters allowed"))
            else:
                if not allow_multiple or (
                    "properties" not in other_extensions and ("sld" in other_extensions or "xml" in other_extensions)
                ):
                    return valid_extensions + other_extensions
                else:
                    return ("zip-mosaic",)
        else:
            return None


def validate_raster_zip(zip_django_file):
    valid_extensions = None
    with zipfile.ZipFile(zip_django_file, allowZip64=True) as zip_handler:
        contents = zip_handler.namelist()
        valid_extensions = validate_raster(contents, allow_multiple=True)
    if valid_extensions:
        if "zip-mosaic" not in valid_extensions:
            return ("zip",)
        else:
            return ("zip-mosaic",)
    return None
