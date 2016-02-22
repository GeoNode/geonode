from geonode import settings
from geonode import GeoNodeException
from geonode.geoserver.helpers import ogc_server_settings
from geoserver.catalog import Catalog
from geonode.layers.models import Style
from geonode.layers.models import Layer
from geonode.geoserver.helpers import http_client
from geonode.layers.utils import create_thumbnail
# cat = Catalog("http://192.168.56.101:8080/geoserver/rest", username="admin", password="geoserver")
# style = cat.get_style("fhm")
# layer = cat.get_layer("bulacan_fh25yr_10m_1")
# print "Default style: %s" % layer.default_style.name
# cat.create_style("angono_fh100yr_10m",open("geoserver/data/styles/fhm.sld").read(),overwrite=True)
# print "changed style: %s" % layer.default_style.name
# style.sld_url("geoserver/data/styles/fhm.sld"
#sld_body, change text of style in geonode
#default_style = style
#upload fhm in geoserver, geonode

cat = Catalog("http://192.168.56.101:8080/geoserver/rest", username="admin", password="geoserver")
layer_list = Layer.objects.filter(name__icontains="fh")
for layer in layer_list
    if layer is not None:
        gs_style = cat.get_style(layer.name)
        gs_layer = cat.get_layer(layer.name)
        cat.delete(gs_style)
        cat.delete(gs_layer)
        style = Style.objects.get(name=layer.name)
        style.delete()
        layer.delete()


# valenzuela = Layer.objects.get(name="valenzuela_fh100yr_10m_5")
# params = {
#     'layers': valenzuela.typename.encode('utf-8'),
#     'format': 'image/png8',
#     'width': 200,
#     'height': 150,
# }
# p = "&".join("%s=%s" % item for item in params.items())
# thumbnail_remote_url = ogc_server_settings.PUBLIC_LOCATION + \
#     "wms/reflect?" + p
# thumbnail_create_url = ogc_server_settings.PUBLIC_LOCATION + \
#     "wms/reflect?" + p
# print "%s" % thumbnail_remote_url
# # print "%s" % thumbnail_create_url
# create_thumbnail(valenzuela, thumbnail_remote_url, thumbnail_remote_url, ogc_client=http_client)
