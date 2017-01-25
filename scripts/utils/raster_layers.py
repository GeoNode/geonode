from geonode.settings import GEONODE_APPS
import geonode.settings as settings
import os, traceback
from geonode.layers.models import Layer
from pprint import pprint
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")

ctr = 1
layers = Layer.objects.all()
with open('raster_layers.log','w') as log_file:
    for layer in layers:
        if layer.is_vector() is False:
            print '',ctr,'', layer.name, '- will delete links'
            print >>log_file,'',ctr,'', layer.name, '- will delete links'
            try:
                layer.link_set.all().delete()
                layer.save()
            except Exception:
                print traceback.print_exc()
                print >> log_file,traceback.print_exc()
            ctr+=1



# import traceback
# from geonode.layers.models import Layer
# ctr=1
# layers = Layer.objects.all()
# for layer in layers:
#     if layer.is_vector() is False:
#         print '',ctr,'', layer.name, '- will delete links'
#         try:
#             layer.link_set.all().delete()
#             layer.save()
#         except Exception:
#             print traceback.print_exc()
#         ctr+=1
#                 
