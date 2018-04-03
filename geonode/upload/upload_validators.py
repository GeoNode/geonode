# -*- coding: utf-8 -*-
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

from __future__ import division

from collections import namedtuple
import os.path
import logging
import zipfile

from django import forms
from django.utils.translation import ugettext as _

from ..geoserver.helpers import ogc_server_settings
from . import files
from .utils import get_kml_doc

logger = logging.getLogger(__name__)

ShapefileAux = namedtuple("ShapefileAux", [
    "extension",
    "mandatory"
])


def _supported_type(ext, supported_types):
    return any([type_.matches(ext) for type_ in supported_types])


def validate_uploaded_files(cleaned, uploaded_files, field_spatial_types):
    requires_datastore = () if ogc_server_settings.DATASTORE else (
        'csv',
        'kml')
    types = [t for t in files.types if t.code not in requires_datastore]
    base_ext = os.path.splitext(cleaned["base_file"].name)[-1].lower()[1:]
    if not _supported_type(base_ext, types) and base_ext.lower() != "zip":
        raise forms.ValidationError(
            "%(supported)s files are supported. You uploaded a "
            "%(uploaded)s file",
            params={
                "supported": " , ".join([t.name for t in types]),
                "uploaded": base_ext
            }
        )
    elif base_ext.lower() == "zip":
        if not zipfile.is_zipfile(cleaned["base_file"]):
            raise forms.ValidationError(_("Invalid zip file detected"))
        valid_extensions = validate_zip(cleaned["base_file"])
    elif base_ext.lower() == "kmz":
        if not zipfile.is_zipfile(cleaned["base_file"]):
            raise forms.ValidationError(_("Invalid kmz file detected"))
        valid_extensions = validate_kmz(
            cleaned["base_file"])
    elif base_ext.lower() == "shp":
        file_paths = [f.name for f in uploaded_files]
        valid_extensions = validate_shapefile_components(
            file_paths)
    elif base_ext.lower() == "kml":
        valid_extensions = validate_kml(uploaded_files)
    else:  # default behavior just assumes files are valid
        valid_extensions = []
        for field_name in field_spatial_types:
            django_file = cleaned.get(field_name)
            try:
                extension = os.path.splitext(django_file.name)[1][1:]
                valid_extensions.append(extension)
            except AttributeError:
                pass
    return valid_extensions


def validate_shapefile_components(possible_filenames):
    """Validates that a shapefile can be loaded from the input file paths

    :arg possible_files: Remaining form upload contents
    :type possible_files: list
    :raises: forms.ValidationError

    """

    shp_files = [f for f in possible_filenames if f.lower().endswith(".shp")]
    if len(shp_files) > 1:
        raise forms.ValidationError(_("Only one shapefile per zip is allowed"))
    shape_component = shp_files[0]
    base_name, base_extension = os.path.splitext(
        os.path.basename(shape_component))
    components = [base_extension[1:]]
    shapefile_additional = [
        ShapefileAux(extension="dbf", mandatory=True),
        ShapefileAux(extension="shx", mandatory=True),
        ShapefileAux(extension="prj", mandatory=False),
        ShapefileAux(extension="xml", mandatory=False),
        ShapefileAux(extension="sld", mandatory=False),
    ]
    for additional_component in shapefile_additional:
        for path in possible_filenames:
            additional_name = os.path.splitext(os.path.basename(path))[0]
            matches_main_name = additional_name == base_name
            extension = os.path.splitext(path)[1][1:].lower()
            found_component = extension == additional_component.extension
            if found_component and matches_main_name:
                components.append(additional_component.extension)
                break
        else:
            if additional_component.mandatory:
                raise forms.ValidationError(
                    "Could not find {!r} file, which is mandatory for "
                    "shapefile uploads".format(
                        additional_component.extension)
                )
    logger.debug("shapefile components: {}".format(components))
    return components


def validate_kml(possible_files):
    """Validate uploaded KML file and a possible image companion file

    KML files that specify vectorial data typers are uploaded standalone.
    However, if the KML specifies a GroundOverlay type (raster) they are
    uploaded together with a raster file.

    """

    kml_file = [
        f for f in possible_files if f.name.lower().endswith(".kml")][0]
    other = [
        f.name for f in possible_files if not f.name.lower().endswith(".kml")]
    kml_file.seek(0)
    kml_bytes = kml_file.read()
    return _validate_kml_bytes(kml_bytes, other)


def validate_kmz(kmz_django_file):
    with zipfile.ZipFile(kmz_django_file) as zip_handler:
        zip_contents = zip_handler.namelist()
        kml_files = [i for i in zip_contents if i.lower().endswith(".kml")]
        if len(kml_files) > 1:
            raise forms.ValidationError(
                _("Only one kml file per kmz is allowed"))
        try:
            kml_zip_path = kml_files[0]
            kml_bytes = zip_handler.read(kml_zip_path)
        except IndexError:
            raise forms.ValidationError(
                _("Could not find any kml files inside the uploaded kmz"))
    other_filenames = [
        i for i in zip_contents if not i.lower().endswith(".kml")]
    _validate_kml_bytes(kml_bytes, other_filenames)
    return ("kmz",)


def validate_zip(zip_django_file):
    with zipfile.ZipFile(zip_django_file) as zip_handler:
        contents = zip_handler.namelist()
        validate_shapefile_components(contents)
    return ("zip",)


def _validate_kml_bytes(kml_bytes, other_files):
    kml_doc, namespaces = get_kml_doc(kml_bytes)
    ground_overlays = kml_doc.xpath(
        "//kml:GroundOverlay", namespaces=namespaces)
    if len(ground_overlays) > 1:
        raise forms.ValidationError(
            _("kml files with more than one GroundOverlay are not supported"))
    elif len(ground_overlays) == 1:
        try:
            image_path = ground_overlays[0].xpath(
                "kml:Icon/kml:href/text()", namespaces=namespaces)[0].strip()
        except IndexError:
            image_path = ""
        logger.debug("image_path: {}".format(image_path))
        logger.debug("other_files: {}".format(other_files))
        if image_path not in other_files:
            raise forms.ValidationError(
                _("Ground overlay image declared in kml file cannot be found"))
        result = ("kml", os.path.splitext(image_path)[-1][1:])
    else:
        result = ("kml", )
    return result
