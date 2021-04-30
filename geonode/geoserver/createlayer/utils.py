# -*- coding: utf-8 -*-
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
from django.template.defaultfilters import slugify

from geonode import GeoNodeException
from geonode.layers.models import Layer
from geonode.layers.utils import get_valid_name
from geonode.geoserver.helpers import (
    gs_catalog,
    ogc_server_settings,
    create_geoserver_db_featurestore)


logger = logging.getLogger(__name__)

BBOX = [-180, 180, -90, 90]
DATA_QUALITY_MESSAGE = "Created with GeoNode"


def create_layer(name, title, owner_name, geometry_type, attributes=None):
    """
    Create an empty layer in GeoServer and register it in GeoNode.
    """
    # first validate parameters
    if geometry_type not in ('Point', 'LineString', 'Polygon'):
        msg = 'geometry must be Point, LineString or Polygon'
        logger.error(msg)
        raise GeoNodeException(msg)
    name = get_valid_name(name)
    # we can proceed
    logger.debug('Creating the layer in GeoServer')
    workspace, datastore = create_gs_layer(name, title, geometry_type, attributes)
    logger.debug('Creating the layer in GeoNode')
    return create_gn_layer(workspace, datastore, name, title, owner_name)


def create_gn_layer(workspace, datastore, name, title, owner_name):
    """
    Associate a layer in GeoNode for a given layer in GeoServer.
    """
    owner = get_user_model().objects.get(username=owner_name)

    layer = Layer.objects.create(
        name=name,
        workspace=workspace.name,
        store=datastore.name,
        storeType='dataStore',
        alternate=f'{workspace.name}:{name}',
        title=title,
        owner=owner,
        uuid=str(uuid.uuid4()),
        bbox_x0=BBOX[0],
        bbox_x1=BBOX[1],
        bbox_y0=BBOX[2],
        bbox_y1=BBOX[3],
        data_quality_statement=DATA_QUALITY_MESSAGE,
    )

    if settings.ADMIN_MODERATE_UPLOADS:
        layer.is_approved = False
    if settings.RESOURCE_PUBLISHING:
        layer.is_published = False

    layer.save()
    return layer


def get_attributes(geometry_type, json_attrs=None):
    """
    Convert a json representation of attributes to a Python representation.

    parameters:

    json_attrs
    {
      "field_str": "string",
      "field_int": "integer",
      "field_date": "date",
      "field_float": "float"
    }

    geometry_type: a string which can be "Point", "LineString" or "Polygon"

    Output:
    [
         ['the_geom', u'com.vividsolutions.jts.geom.Polygon', {'nillable': False}],
         ['field_str', 'java.lang.String', {'nillable': True}],
         ['field_int', 'java.lang.Integer', {'nillable': True}],
         ['field_date', 'java.util.Date', {'nillable': True}],
         ['field_float', 'java.lang.Float', {'nillable': True}]
    ]
    """

    lattrs = []
    gattr = []
    gattr.append('the_geom')
    gattr.append(f'com.vividsolutions.jts.geom.{geometry_type}')
    gattr.append({'nillable': False})
    lattrs.append(gattr)
    if json_attrs:
        jattrs = json.loads(json_attrs)
        for jattr in jattrs.items():
            lattr = []
            attr_name = slugify(jattr[0])
            attr_type = jattr[1].lower()
            if len(attr_name) == 0:
                msg = f'You must provide an attribute name for attribute of type {attr_type}'
                logger.error(msg)
                raise GeoNodeException(msg)
            if attr_type not in ('float', 'date', 'string', 'integer'):
                msg = f'{attr_type} is not a valid type for attribute {attr_name}'
                logger.error(msg)
                raise GeoNodeException(msg)
            if attr_type == 'date':
                attr_type = f"java.util.{attr_type[:1].upper()}{attr_type[1:]}"
            else:
                attr_type = f"java.lang.{attr_type[:1].upper()}{attr_type[1:]}"
            lattr.append(attr_name)
            lattr.append(attr_type)
            lattr.append({'nillable': True})
            lattrs.append(lattr)
    return lattrs


def get_or_create_datastore(cat, workspace=None, charset="UTF-8"):
    """
    Get a PostGIS database store or create it in GeoServer if does not exist.
    """
    dsname = ogc_server_settings.datastore_db['NAME']
    ds = create_geoserver_db_featurestore(store_name=dsname, workspace=workspace)
    return ds


def create_gs_layer(name, title, geometry_type, attributes=None):
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
    if datastore.type != 'PostGIS':
        msg = ("To use the createlayer application you must use PostGIS")
        logger.error(msg)
        raise GeoNodeException(msg)

    # check if layer is existing
    resources = datastore.get_resources()
    for resource in resources:
        if resource.name == name:
            msg = f"There is already a layer named {name} in {workspace}"
            logger.error(msg)
            raise GeoNodeException(msg)

    attributes = get_attributes(geometry_type, attributes)
    attributes_block = "<attributes>"
    for spec in attributes:
        att_name, binding, opts = spec
        nillable = opts.get("nillable", False)
        attributes_block += ("<attribute>"
                             "<name>{name}</name>"
                             "<binding>{binding}</binding>"
                             "<nillable>{nillable}</nillable>"
                             "</attribute>").format(name=att_name, binding=binding, nillable=nillable)
    attributes_block += "</attributes>"

    # TODO implement others srs and not only EPSG:4326
    xml = ("<featureType>"
           "<name>{name}</name>"
           "<nativeName>{native_name}</nativeName>"
           "<title>{title}</title>"
           "<srs>EPSG:4326</srs>"
           "<latLonBoundingBox><minx>{minx}</minx><maxx>{maxx}</maxx><miny>{miny}</miny><maxy>{maxy}</maxy>"
           "<crs>EPSG:4326</crs></latLonBoundingBox>"
           "{attributes}"
           "</featureType>").format(
        name=name, native_name=native_name,
        title=title,
        minx=BBOX[0], maxx=BBOX[1], miny=BBOX[2], maxy=BBOX[3],
        attributes=attributes_block)

    url = f'{ogc_server_settings.rest}/workspaces/{workspace.name}/datastores/{datastore.name}/featuretypes'
    headers = {'Content-Type': 'application/xml'}
    _user, _password = ogc_server_settings.credentials
    req = requests.post(url, data=xml, headers=headers, auth=(_user, _password))
    if req.status_code != 201:
        logger.error(f'Request status code was: {req.status_code}')
        logger.error(f'Response was: {req.text}')
        raise Exception(f"Layer could not be created in GeoServer {req.text}")

    return workspace, datastore
