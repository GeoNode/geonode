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
layer_list = Layer.objects.filter(name__icontains='fh')
fhm_style = cat.get_style("fhm")
for layer in layer_list:
    if layer is not None:
        gs_layer = cat.get_layer(layer.name)
        gs_layer._set_default_style(fhm_style.name)
        cat.save(gs_layer)
        #erase in geoserver the default layer_list
        gs_style = cat.get_style(layer.name)
        cat.delete(gs_style)
        style = Style.objects.get(name=layer.name)
        style.delete()


    layer_list = Layer.objects.filter(name__icontains='fh')
    fhm_style = cat.get_style("fhm")
    for layer in layer_list:
        gs_layer = cat.get_layer(layer.name)
        gs_layer._set_default_style(fhm_style.name)
        cat.save(gs_layer) #save in geoserver
        layer.sld_body = fhm_style.sld_body
        layer.save() #save in geonode
        try:
            gs_style = cat.get_style(layer.name)
            cat.delete(gs_style) #erase in geoserver the default layer_list
            gn_style = Style.objects.get(name=layer.name)
            gn_style.delete()#erase in geonode
        except:
            print "Style does not exist"

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
# gn_style_list = Style.objects.filter(name__icontains='fh').exclude(Q(name__icontains="fhm")|Q(sld_body__icontains='<sld:CssParameter name="fill">#ffff00</sld:CssParameter>'))
# # gn_style_list = Style.objects.filter(name__icontains='fh').exclude(Q(name__icontains="fhm"))
# gs_style = None
# fh_styles_count = len(gn_style_list)
# ctr = 0
# if gn_style_list is not None:
#     fhm_style = cat.get_style("fhm")
#     for gn_style in gn_style_list:
#         #change style in geoserver
#         try:
#             layer = Layer.objects.get(name=gn_style.name)
#             gs_style  = cat.get_style(gn_style.name)
#             if gs_style is not None:
#                 gs_style  = cat.get_style(gn_style.name)
#                 gs_style.update_body(fhm_style.sld_body)
#             else:
#                 cat.create_style(gn_style.name,fhm.sld_body)
#             #change style in geonode
#             gn_style.sld_body = fhm_style.sld_body
#             gn_style.save()
#             #for updating thumbnail
#             params = {
#                 'layers': layer.typename.encode('utf-8'),
#                 'format': 'image/png8',
#                 'width': 200,
#                 'height': 150,
#             }
#             p = "&".join("%s=%s" % item for item in params.items())
#             thumbnail_remote_url = ogc_server_settings.PUBLIC_LOCATION + \
#                 "wms/reflect?" + p
#             # thumbnail_create_url = ogc_server_settings.LOCATION + \
#             #     "wms/reflect?" + p
#             create_thumbnail(layer, thumbnail_remote_url, thumbnail_remote_url, ogc_client=http_client)
#             ctr+=1
#             print "'{0}' out of '{1}' : Updated style for '{2}' ".format(ctr,fh_styles_count,gn_style.name)
#         except Exception as e:
#             err_msg = str(e)
#             if "Layer matching query does not exist" in err_msg:
#                 gn_style.delete()
