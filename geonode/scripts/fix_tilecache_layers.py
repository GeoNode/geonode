import json

from django.core.exceptions import ObjectDoesNotExist

from geonode.maps.models import Layer, Map, MapLayer


layers_dict = {
    '1895_coast': 'Boston_1895',
    '1924_ethno': 'Africa_ethno_1924',
    '1930_admin_col': 'afrique_1930_detailed_admin',
    'afrique_1930_detailed_admin': 'afrique_1930_detailed_admin',
    'ams_250k': 'ams_china',
    'century': 'Century',
    'century_col': 'Century',
    'croquis': 'croquis',
    'desisle': 'deslisle',
    'desnos': 'desnos',
    'dewit': 'dewitt',
    'Free': 'Freetown',
    'hondio': 'Hondio',
    'hopkins': 'Hopkins_1875',
    'ife': 'ife',
    'landscan': 'landscan_africa_2',
    'mapc_towns': 'mapc_towns3',
    'ng_100': 'Nigeria_100k',
    'onc_all': 'ONC',
    'Russian500k': 'ru500k',
    'soils': 'soils_africa',
    'tibet_100k': 'tibet',
    'trade': 'trade_africa2',
    'zoning': 'zoning_boston',
}


class TileCacheLayersFixer(object):
    layers_replaced = set([])
    layers_not_in_wm = set([])
    layers_not_in_dict = set([])

    def get_impacted_maps(self):
        layers = MapLayer.objects.filter(ows_url__contains='cga-5.hmdc.harvard.edu')
        layer_maps_dict = {}
        for layer in layers:
            maps = []
            if layer.name in layer_maps_dict:
                maps = layer_maps_dict[layer.name]
            maps.append(layer.map_id)
            layer_maps_dict[layer.name] = maps
        for layer in layer_maps_dict:
            print layer
            maps = sorted(layer_maps_dict[layer])
            print(', '.join(str(x) for x in maps))

    def fix_all_maps(self, commit=False):
        for map in Map.objects.all().order_by('id'):
            self.fix_map(map.id, commit)

    def fix_map(self, map_id, commit=False):
        """
        Fixing all of the layers for a given map.
        """
        map = Map.objects.get(id=map_id)
        print 'Fixing map: %s' % map.id
        for layer in map.layer_set.filter(ows_url__contains='cga-5.hmdc.harvard.edu'):
            jlayer = json.loads(layer.layer_params)
            # 1: new_name in ['capability']['tileSets'][0]['layers']
            # 2: new_name in ['title']
            name = layer.name
            if name in layers_dict:
                new_name = layers_dict[name]
                new_ows_url = 'http://worldmap.harvard.edu/geoserver/wms'
                result, new_layer_params = self.get_layer_params(new_name, jlayer['title'])
                if result:
                    self.layers_replaced.add(name)
                    new_source_params = '{"restUrl": "/gs/rest", "title": "GeoNode Source", "ptype": "gxp_gnsource", "id": "%s"}' % map.layer_set.all().count()
                    if commit:
                        layer.ows_url = new_ows_url
                        layer.name = 'geonode:%s' % new_name
                        layer.layer_params = new_layer_params
                        layer.source_params = new_source_params
                        layer.save()
                        print 'Layer with id %s named %s replaced with %s in group %s' % (layer.id, name, new_name, layer.group)
                else:
                    self.layers_not_in_wm.add(name)
            else:
                print '***** There is not a layer named %s in the dictionary! *****' % name
                self.layers_not_in_dict.add(name)

    def get_layer_params(self, layer_name, layer_title):
        """
        Get layer_params for an ecw layer given its name.
        """
        try:
            layer = Layer.objects.get(typename='geonode:%s' % layer_name)
        except ObjectDoesNotExist:
            print '***** In GeoNode we do not have a layer named geonode:%s *****' % layer_name
            return False, None
        layer_params = '{"selected": true, "title": " %s", "url": "http://worldmap.harvard.edu/geoserver/wms", \
            "tiled": true, "local": true, \
            "llbbox": [%s]}' % (layer_title, layer.bbox)
        return True, layer_params

    def print_report(self):
        print 'Report:'
        print 'Layers replaced: %s' % ", ".join(str(e) for e in self.layers_replaced)
        print 'Layers not in WorldMap: %s' % ", ".join(str(e) for e in self.layers_not_in_wm)
        print 'Layers not in dictionary: %s' % ", ".join(str(e) for e in self.layers_not_in_dict)
