from geonode.maps.models import Map, MapLayer
from django.conf import settings

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

    if 'geonode.geoserver' in settings.INSTALLED_APPS:
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
            transparent=ml['stack_order'],
            visibility=ml['stack_order'],
        )
