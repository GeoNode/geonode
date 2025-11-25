#########################################################################
#
# Copyright (C) 2024 OSGeo
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
import logging

import xml.etree.ElementTree as ET
from geonode.upload.api.exceptions import ImportException


logger = logging.getLogger("importer")

BBOX = [-180, -90, 180, 90]
DATA_QUALITY_MESSAGE = "Created with GeoNode"
ATTRIBUTE_TYPE_MAP = {
    "string": "java.lang.String",
    "float": "java.lang.Float",
    "integer": "java.lang.Integer",
    "date": "java.sql.Date",
    "Point": "com.vividsolutions.jts.geom.Point",
    "LineString": "com.vividsolutions.jts.geom.LineString",
    "Polygon": "com.vividsolutions.jts.geom.Polygon",
}
RESTRICTION_OPTIONS_TYPE_MAP = {"string": "string", "float": "float", "integer": "int"}

base_xml = (
    "<featureType>"
    "<name>{name}</name>"
    "<nativeName>{name}</nativeName>"
    "<title>{name}</title>"
    "<srs>EPSG:4326</srs>"
    f"<nativeBoundingBox><minx>{BBOX[0]}</minx><maxx>{BBOX[2]}</maxx><miny>{BBOX[1]}</miny><maxy>{BBOX[3]}</maxy><crs>EPSG:4326</crs></nativeBoundingBox>"
    f"<latLonBoundingBox><minx>{BBOX[0]}</minx><maxx>{BBOX[2]}</maxx><miny>{BBOX[1]}</miny><maxy>{BBOX[3]}</maxy>"
    "<crs>EPSG:4326</crs></latLonBoundingBox>"
    "<attributes></attributes>"
    "</featureType>"
)


def validate_attributes(attributes_dict):
    for name in attributes_dict:
        info = attributes_dict[name]
        attr_type = info.get("type")
        attr_options = info.get("options")
        attr_range = info.get("range")
        if len(name) == 0:
            msg = f"You must provide an attribute name for attribute of type {attr_type}"
            logger.error(msg)
            raise ImportException(msg)
        if not ATTRIBUTE_TYPE_MAP.get(attr_type):
            msg = f"{attr_type} is not a valid type for attribute {name}"
            logger.error(msg)
            raise ImportException(msg)
        if attr_type == "date" and attr_options:
            msg = f"{attr_type} does not support options restriction"
            logger.error(msg)
            raise ImportException(msg)
        if attr_type in ["date", "string"] and attr_range:
            msg = f"{attr_type} does not support range restriction"
            logger.error(msg)
            raise ImportException(msg)
    return True


def should_apply_restrictions(attributes_dict):
    for name in attributes_dict:
        info = attributes_dict[name]
        attr_options = info.get("options")
        attr_range = info.get("range")
        if attr_options or attr_range:
            return True
    return False


def add_attributes_to_xml(attributes_dict, xml):
    root = ET.fromstring(xml)
    attributes_tag = root.find("attributes")
    for name in attributes_dict:
        info = attributes_dict[name]
        attr_name = name
        attr_type = ATTRIBUTE_TYPE_MAP.get(info.get("type"))
        attr_nillable = "false"
        if info.get("nillable"):
            attr_nillable = "true"
        attribute_tag = ET.SubElement(attributes_tag, "attribute")
        ET.SubElement(attribute_tag, "name").text = f"{attr_name}"
        ET.SubElement(attribute_tag, "binding").text = f"{attr_type}"
        ET.SubElement(attribute_tag, "nillable").text = f"{attr_nillable}"
    return ET.tostring(root)


def apply_restrictions_to_xml(attributes_dict, xml):
    root = ET.fromstring(xml)
    attributes_tag = root.find("attributes")
    for attribute in attributes_tag.findall("attribute"):
        name = attribute.find("name").text
        info = attributes_dict.get(name, None)
        if info:
            restrictions_range = info.get("range")
            if restrictions_range:
                min_restrictions_range = restrictions_range.get("min", None)
                max_restrictions_range = restrictions_range.get("max", None)
                range_tag = ET.SubElement(attribute, "range")
                if min_restrictions_range is not None:
                    ET.SubElement(range_tag, "min").text = f"{min_restrictions_range}"
                if max_restrictions_range is not None:
                    ET.SubElement(range_tag, "max").text = f"{max_restrictions_range}"
            restrictions_options = info.get("options")
            if restrictions_options:
                options_tag = ET.SubElement(attribute, "options")
                for option in restrictions_options:
                    ET.SubElement(options_tag, RESTRICTION_OPTIONS_TYPE_MAP.get(info.get("type"))).text = f"{option}"
    return ET.tostring(root)
