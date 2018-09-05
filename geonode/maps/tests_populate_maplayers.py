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

from geonode import geoserver, qgis_server  # noqa
from geonode.utils import check_ogc_backend
from geonode.maps.models import Map, MapLayer

maplayers = [{"fixed": False,
              "group": "background",
              "layer_params": "",
              "map": 'GeoNode Default Map',
              "name": "geonode:CA",
              "ows_url": "http://localhost:8080/geoserver/wms",
              "source_params": "",
              "transparent": False,
              "stack_order": 0,
              "visibility": True,
              "opacity": 1,
              },
             {"fixed": True,
              "group": "background",
              "layer_params": "{\"args\": [\"bluemarble\", \"http://maps.opengeo.org/geowebcache/service/wms\", \
              {\"layers\": [\"bluemarble\"], \"tiled\": true, \"tilesOrigin\": [-20037508.34, -20037508.34],\
              \"format\": \"image/png\"}, {\"buffer\": 0}], \"type\": \"OpenLayers.Layer.WMS\"}",
              "map": 'GeoNode Default Map',
              "name": None,
              "opacity": 1,
              "source_params": "{\"ptype\": \"gxp_olsource\"}",
              "stack_order": 0,
              "transparent": False,
              "visibility": True},
             {"fixed": True,
              "group": "background",
              "layer_params": "{\"args\": [\"geonode:CA\", \"http://localhost:8080/geoserver/wms\", {\"layers\": \
              [\"geonode:CA\"], \"tiled\": true, \"tilesOrigin\": [-20037508.34, -20037508.34], \"format\":\
               \"image/png\"}, {\"buffer\": 0}], \"type\": \"OpenLayers.Layer.WMS\"}",
              "map": 'GeoNode Default Map',
              "name": None,
              "opacity": 1,
              "source_params": "{\"ptype\": \"gxp_olsource\"}",
              "stack_order": 1,
              "transparent": False,
              "visibility": False},
             {"fixed": True,
              "group": "background",
              "layer_params": "{}",
              "map": 'GeoNode Default Map',
              "name": "SATELLITE",
              "opacity": 1,
              "source_params": "{\"apiKey\":\
               \"ABQIAAAAkofooZxTfcCv9Wi3zzGTVxTnme5EwnLVtEDGnh-lFVzRJhbdQhQgAhB1eT_2muZtc0dl-ZSWrtzmrw\", \"ptype\":\
                \"gxp_googlesource\"}",
              "stack_order": 2,
              "transparent": False,
              "visibility": False},
             {"fixed": True,
              "group": "background",
              "layer_params": "{\"args\": [\"No background\"], \"type\": \"OpenLayers.Layer\"}",
              "map": 'GeoNode Default Map',
              "name": None,
              "opacity": 1,
              "source_params": "{\"ptype\": \"gxp_olsource\"}",
              "stack_order": 3,
              "transparent": False,
              "visibility": False}]


def create_maplayers():
    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        from django.db.models import signals
        from geonode.geoserver.signals import geoserver_pre_save_maplayer
        from geonode.geoserver.signals import geoserver_post_save_map
        signals.pre_save.disconnect(
            geoserver_pre_save_maplayer,
            sender=MapLayer)
        signals.post_save.disconnect(geoserver_post_save_map, sender=Map)

    for ml in maplayers:
        MapLayer.objects.create(
            fixed=ml['fixed'],
            group=ml['group'],
            name=ml['name'],
            layer_params=ml['layer_params'],
            map=Map.objects.get(title=ml['map']),
            source_params=ml['source_params'],
            stack_order=ml['stack_order'],
            opacity=ml['opacity'],
            transparent=True,
            visibility=True
        )
