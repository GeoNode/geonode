#########################################################################
#
# Copyright (C) 2017 OSGeo
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
import json
import uuid
import logging
import requests

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Polygon
import xml.etree.ElementTree as ET

from geonode import GeoNodeException
from geonode.layers.models import Dataset
from geonode.layers.utils import get_valid_name
from geonode.resource.manager import resource_manager
from geonode.geoserver.helpers import gs_catalog, ogc_server_settings, create_geoserver_db_featurestore
from geonode.upload.handlers.utils import create_alternate
import uuid

logger = logging.getLogger(__name__)

BBOX = [-180, -90, 180, 90]
DATA_QUALITY_MESSAGE = "Created with GeoNode"
ATTRIBUTE_TYPE_MAP = {
    "string": "java.lang.String",
    "float": "java.lang.Float",
    "integer": "java.lang.Integer",
    "date": "java.util.Date",
    "Point": "com.vividsolutions.jts.geom.Point",
    "LineString": "com.vividsolutions.jts.geom.LineString",
    "Polygon": "com.vividsolutions.jts.geom.Polygon"
}
RESTRICTION_OPTIONS_TYPE_MAP = {
    "string": "string",
    "float": "float",
    "integer": "int"
}


def create_dataset(title, owner_name, geometry_type, attributes=None):
    """
    Create an empty layer in GeoServer and register it in GeoNode.
    """
    # first validate parameters
    if geometry_type not in ("Point", "LineString", "Polygon"):
        msg = "geometry must be Point, LineString or Polygon"
        logger.error(msg)
        raise GeoNodeException(msg)
    execution_id = str(uuid.uuid4())
    name = create_alternate(get_valid_name(title.replace(".", "_").lower()), execution_id)
    # we can proceed
    logger.debug("Creating the layer in GeoServer")
    workspace, datastore = create_gs_dataset(name, title, geometry_type, attributes)
    logger.debug("Creating the layer in GeoNode")
    return create_gn_dataset(workspace, datastore, name, title, owner_name)


def create_gn_dataset(workspace, datastore, name, title, owner_name):
    """
    Associate a layer in GeoNode for a given layer in GeoServer.
    """
    owner = get_user_model().objects.get(username=owner_name)

    layer = resource_manager.create(
        str(uuid.uuid4()),
        resource_type=Dataset,
        defaults=dict(
            name=name,
            workspace=workspace.name,
            store=datastore.name,
            subtype="vector",
            alternate=f"{workspace.name}:{name}",
            title=title,
            owner=owner,
            srid="EPSG:4326",
            bbox_polygon=Polygon.from_bbox(BBOX),
            ll_bbox_polygon=Polygon.from_bbox(BBOX),
            data_quality_statement=DATA_QUALITY_MESSAGE,
        ),
    )

    to_update = {}
    if settings.ADMIN_MODERATE_UPLOADS:
        to_update["is_approved"] = to_update["was_approved"] = False
    if settings.RESOURCE_PUBLISHING:
        to_update["is_published"] = to_update["was_published"] = False

    resource_manager.update(layer.uuid, instance=layer, vals=to_update)
    return layer

def get_or_create_datastore(cat, workspace=None, charset="UTF-8"):
    """
    Get a PostGIS database store or create it in GeoServer if does not exist.
    """
    dsname = ogc_server_settings.datastore_db["NAME"]
    ds = create_geoserver_db_featurestore(store_name=dsname, workspace=workspace)
    return ds

def validate_attributes(attributes_dict):
    for name in attributes_dict:
        info = attributes_dict[name]
        attr_type = info.get("type")
        attr_options = info.get("options")
        attr_range = info.get("range")
        if len(name) == 0:
            msg = f"You must provide an attribute name for attribute of type {attr_type}"
            logger.error(msg)
            raise GeoNodeException(msg)
        if not ATTRIBUTE_TYPE_MAP.get(attr_type):
            msg = f"{attr_type} is not a valid type for attribute {name}"
            logger.error(msg)
            raise GeoNodeException(msg)
        if attr_type == "date" and attr_options:
            msg = f"{attr_type} does not support options restriction"
            logger.error(msg)
            raise GeoNodeException(msg)
        if attr_type in ["date", "string"] and attr_range:
            msg = f"{attr_type} does not support range restriction"
            logger.error(msg)
            raise GeoNodeException(msg)
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
                if min_restrictions_range != None:
                    ET.SubElement(range_tag, "min").text = f"{min_restrictions_range}"
                if max_restrictions_range != None:
                    ET.SubElement(range_tag, "max").text = f"{max_restrictions_range}"
            restrictions_options = info.get("options")
            if restrictions_options:
                options_tag = ET.SubElement(attribute, "options")
                for option in restrictions_options:
                    ET.SubElement(options_tag, RESTRICTION_OPTIONS_TYPE_MAP.get(info.get("type"))).text = f"{option}"
    return ET.tostring(root)

def create_gs_dataset(name, title, geometry_type, attributes=None):
    """
    Create an empty PostGIS layer in GeoServer with a given name, title,
    geometry_type and attributes.
    """

    native_name = name
    cat = gs_catalog

    # get workspace and store
    workspace = cat.get_default_workspace()

    # get (or create the datastore)
    datastore = get_or_create_datastore(cat, workspace)

    # check if datastore is of PostGIS type
    if datastore.type != "PostGIS":
        msg = "To use the createlayer application you must use PostGIS"
        logger.error(msg)
        raise GeoNodeException(msg)

    # check if layer is existing
    resources = datastore.get_resources()
    for resource in resources:
        if resource.name == name:
            msg = f"There is already a layer named {name} in {workspace}"
            logger.error(msg)
            raise GeoNodeException(msg)

    # TODO implement others srs and not only EPSG:4326
    base_xml = (
        "<featureType>"
        f"<name>{name}</name>"
        f"<nativeName>{native_name}</nativeName>"
        f"<title>{title}</title>"
        "<srs>EPSG:4326</srs>"
        f"<latLonBoundingBox><minx>{BBOX[0]}</minx><maxx>{BBOX[2]}</maxx><miny>{BBOX[1]}</miny><maxy>{BBOX[3]}</maxy>"
        "<crs>EPSG:4326</crs></latLonBoundingBox>"
        "<attributes></attributes>"
        "</featureType>"
    )

    # structure example for attributes_dict
    # {
    #   "field_str": { "type": "string" },
    #   "field_int": { "type": "integer" },
    #   "field_date": { "type":"date" },
    #   "field_float": { "type": "float" },
    #   "field_str_options": { "type": "string", "nillable": False, "options": ["A", "B", "C"] },
    #   "field_int_options": { "type": "integer", "nillable": False, "options": [1, 2, 3] },
    #   "field_int_range": { "type": "integer", "nillable": False, "range": { "min": 1, "max": 10 } },
    #   "field_float_options": { "type": "integer", "nillable": False, "options": [1.2, 2.4, 3.6] },
    #   "field_float_range": { "type": "integer", "nillable": False, "range": { "min": 1.5, "max": 10.5 } },
    # }
    attributes_dict = json.loads(attributes)

    validate_attributes(attributes_dict)

    xml = add_attributes_to_xml({
        **attributes_dict,
        # include geometry as an available attribute
        "geom": {
            "type": geometry_type,
            "nillable": False
        }
    }, base_xml)

    if should_apply_restrictions(attributes_dict):
        xml = apply_restrictions_to_xml(attributes_dict, xml)

    url = f"{ogc_server_settings.rest}/workspaces/{workspace.name}/datastores/{datastore.name}/featuretypes"
    headers = { "Content-Type": "application/xml" }
    _user, _password = ogc_server_settings.credentials

    req = requests.post(url, data=xml, headers=headers, auth=(_user, _password))
    if req.status_code != 201:
        logger.error(f"Request status code was: {req.status_code}")
        logger.error(f"Response was: {req.text}")
        raise Exception(f"Dataset could not be created in GeoServer {req.text}")

    cat.reload()
    return workspace, datastore
