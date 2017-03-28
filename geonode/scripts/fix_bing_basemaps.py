import json

from django.conf import settings

from geonode.maps.models import MapLayer

def fix_bing_basemaps(commit=False):
    """
    Fix API key in Bing base maps.
    """
    layers = MapLayer.objects.filter(source_params__contains='gxp_bingsource')
    for layer in layers:
        jlayer = json.loads(layer.source_params)
        if 'apiKey' not in jlayer or jlayer['apiKey'] != settings.BING_API_KEY:
            print 'map_id: %s' % layer.map_id
            print 'Wrong API key: %s' % jlayer
            jlayer['apiKey'] = settings.BING_API_KEY
            print 'Correcting to: %s' % jlayer
            if commit:
                layer.source_params = json.dumps(jlayer)
                layer.save()
