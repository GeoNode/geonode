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

import requests
import uuid
import logging
import json

from django.template.defaultfilters import slugify

from geoserver.catalog import Catalog
from geoserver.catalog import FailedRequestError

from geonode import GeoNodeException
from geonode.layers.models import Layer
from geonode.layers.utils import get_valid_name
from geonode.people.models import Profile
from geonode.geoserver.helpers import ogc_server_settings


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
    owner = Profile.objects.get(username=owner_name)

    layer = Layer.objects.create(
        name=name,
        workspace=workspace.name,
        store=datastore.name,
        storeType='dataStore',
        alternate='%s:%s' % (workspace.name, name),
        title=title,
        owner=owner,
        uuid=str(uuid.uuid4()),
        bbox_x0=BBOX[0],
        bbox_x1=BBOX[1],
        bbox_y0=BBOX[2],
        bbox_y1=BBOX[3],
        data_quality_statement=DATA_QUALITY_MESSAGE,
    )
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
    gattr.append('com.vividsolutions.jts.geom.%s' % geometry_type)
    gattr.append({'nillable': False})
    lattrs.append(gattr)
    if json_attrs:
        jattrs = json.loads(json_attrs)
        for jattr in jattrs.items():
            lattr = []
            attr_name = slugify(jattr[0])
            attr_type = jattr[1].lower()
            if len(attr_name) == 0:
                msg = 'You must provide an attribute name for attribute of type %s' % (attr_type)
                logger.error(msg)
                raise GeoNodeException(msg)
            if attr_type not in ('float', 'date', 'string', 'integer'):
                msg = '%s is not a valid type for attribute %s' % (attr_type, attr_name)
                logger.error(msg)
                raise GeoNodeException(msg)
            if attr_type == 'date':
                attr_type = 'java.util.%s' % attr_type[:1].upper() + attr_type[1:]
            else:
                attr_type = 'java.lang.%s' % attr_type[:1].upper() + attr_type[1:]
            lattr.append(attr_name)
            lattr.append(attr_type)
            lattr.append({'nillable': True})
            lattrs.append(lattr)
    return lattrs


def get_or_create_datastore(cat, workspace=None, charset="UTF-8"):
    """
    Get a PostGIS database store or create it in GeoServer if does not exist.
    """

    # TODO refactor this and geoserver.helpers._create_db_featurestore
    # dsname = ogc_server_settings.DATASTORE
    dsname = ogc_server_settings.datastore_db['NAME']
    if not ogc_server_settings.DATASTORE:
        msg = ("To use the createlayer application you must set ogc_server_settings.datastore_db['ENGINE']"
               " to 'django.contrib.gis.db.backends.postgis")
        logger.error(msg)
        raise GeoNodeException(msg)

    try:
        ds = cat.get_store(dsname, workspace)
    except FailedRequestError:
        ds = cat.create_datastore(dsname, workspace=workspace)

    db = ogc_server_settings.datastore_db
    ds.connection_parameters.update(
        {'validate connections': 'true',
         'max connections': '10',
         'min connections': '1',
         'fetch size': '1000',
         'host': db['HOST'],
         'port': db['PORT'] if isinstance(
             db['PORT'], basestring) else str(db['PORT']) or '5432',
         'database': db['NAME'],
         'user': db['USER'],
         'passwd': db['PASSWORD'],
         'dbtype': 'postgis'}
    )

    cat.save(ds)

    # we need to reload the ds as gsconfig-1.0.6 apparently does not populate ds.type
    # using create_datastore (TODO fix this in gsconfig)
    ds = cat.get_store(dsname, workspace)

    return ds


def create_gs_layer(name, title, geometry_type, attributes=None):
    """
    Create an empty PostGIS layer in GeoServer with a given name, title,
    geometry_type and attributes.
    """

    native_name = name
    gs_user = ogc_server_settings.credentials[0]
    gs_password = ogc_server_settings.credentials[1]
    cat = Catalog(ogc_server_settings.internal_rest, gs_user, gs_password)

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
            msg = "There is already a layer named %s in %s" % (name, workspace)
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
                name=name.encode('UTF-8', 'strict'), native_name=native_name.encode('UTF-8', 'strict'),
                title=title.encode('UTF-8', 'strict'),
                minx=BBOX[0], maxx=BBOX[1], miny=BBOX[2], maxy=BBOX[3],
                attributes=attributes_block)

    url = ('%s/workspaces/%s/datastores/%s/featuretypes'
           % (ogc_server_settings.internal_rest, workspace.name, datastore.name))
    headers = {'Content-Type': 'application/xml'}
    req = requests.post(url, data=xml, headers=headers, auth=(gs_user, gs_password))
    if req.status_code != 201:
        logger.error('Request status code was: %s' % req.status_code)
        logger.error('Response was: %s' % req.text)
        raise GeoNodeException("Layer could not be created in GeoServer")

    return workspace, datastore
