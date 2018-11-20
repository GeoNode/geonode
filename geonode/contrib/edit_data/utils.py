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

"""Utilities for managing GeoNode edit data
"""

import requests

from django.conf import settings
from django.template.loader import get_template

from geonode.base.models import ResourceBase
from geonode.utils import bbox_to_wkt

from geoserver.catalog import Catalog


# Used to update the BBOX of geoserver and send a see request
# Takes as input the headers and the layer_name
# Returns status_code of each request
def update_bbox_and_seed(headers, layer_name, store_name):
    # Update the BBOX of layer in geoserver (use of recalculate)
    url = settings.OGC_SERVER['default']['LOCATION'] + "rest/workspaces/geonode/datastores/{store_name}/featuretypes/{layer_name}.xml?recalculate=nativebbox,latlonbbox".format(** {
        'store_name': store_name.strip(),
        'layer_name': layer_name
    })

    xmlstr = """<featureType><enabled>true</enabled></featureType>"""
    status_code_bbox = requests.put(url, headers=headers, data=xmlstr, auth=(settings.OGC_SERVER['default']['USER'], settings.OGC_SERVER['default']['PASSWORD'])).status_code

    # Seed the cache for this layer
    url = settings.OGC_SERVER['default']['LOCATION'] + "gwc/rest/seed/geonode:{layer_name}.xml".format(** {
        'layer_name': layer_name
    })
    xml_path = "edit_data/seedRequest_geom.xml"
    xmlstr = get_template(xml_path).render({
            'workspace': 'geonode',
            'layer_name': layer_name
            })
    status_code_seed = requests.post(url, data=xmlstr, headers=headers, auth=(settings.OGC_SERVER['default']['USER'], settings.OGC_SERVER['default']['PASSWORD'])).status_code
    return status_code_bbox, status_code_seed


# Update the values for BBOX in CSW with the values calculated in geoserver layer
def update_bbox_in_CSW(layer, layer_name):

    # Get the coords from geoserver layer and update the base_resourceBase table
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + "rest", settings.OGC_SERVER['default']['USER'], settings.OGC_SERVER['default']['PASSWORD'])
    resource = cat.get_resource(layer_name, workspace="geonode")
    # use bbox_to_wkt to convert the BBOX coords to the wkt format
    r = bbox_to_wkt(resource.latlon_bbox[0], resource.latlon_bbox[1], resource.latlon_bbox[2], resource.latlon_bbox[3], "4326")
    csw_wkt_geometry = r.split(";", 1)[1]
    # update the base_resourceBase
    resources = ResourceBase.objects.filter(pk=layer.id)
    resources.update(bbox_x0=resource.latlon_bbox[0], bbox_x1=resource.latlon_bbox[1], bbox_y0=resource.latlon_bbox[2], bbox_y1=resource.latlon_bbox[3], csw_wkt_geometry=csw_wkt_geometry)

    return csw_wkt_geometry


#  Returns the store name based on the workspace and the layer name
def get_store_name(layer_name):
    # get the name of the store
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + "rest", settings.OGC_SERVER['default']['USER'], settings.OGC_SERVER['default']['PASSWORD'])
    resource = cat.get_resource(layer_name, workspace='geonode')
    store_name = resource.store.name

    # select the name of the geometry column based on the store type
    if (store_name == "uploaded"):
        geometry_clm = "the_geom"
    else:
        geometry_clm = "shape"


    return store_name, geometry_clm
