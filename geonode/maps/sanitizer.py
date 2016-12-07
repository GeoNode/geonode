import json
from geonode.maps.models import Layer, Map, MapLayer


def fix_broken_wm_map(map_id):
    """
    Fix broken WM layers for a given map.
    """
    map = Map.objects.get(id=map_id)

    for layer in map.layer_set.filter(ows_url__icontains='worldmap.harvard.edu/geoserver/wms'):
        if layer.name is None:
            print 'This layer is None!!!'
        else:
            print 'Fixing layer %s' % layer.name
            print layer.layer_params
            config = json.loads(layer.layer_params)
            title = config['title']
            selected = config['selected']
            new_config = {
                'title': title,
                'selected': selected,
                'tiled': True,
                'local': True
            }
            if 'url' in config:
                new_config['url'] = 'http://worldmap.harvard.edu/geoserver/wms'
            if 'llbbox' in config:
                new_config['llbbox'] = config['llbbox']
            # else:
            #     gn_layer = Layer.objects.get(typename=layer.name)
            #     new_config['llbbox'] = gn_layer.bbox_coords()
            new_config_s = json.dumps(new_config)
            print new_config_s
            layer.layer_params = new_config_s
            layer.save()

def get_broken_wm_maps():
    """
    Detect all WM broken layer in WM.
    """
    broken_wm_maps = []
    for map in Map.objects.all().order_by('id'):
        is_broken = False
        for layer in map.layer_set.filter(ows_url__icontains='worldmap.harvard.edu/geoserver/wms'):
            if layer.name is None:
                #print 'Layer id:%s in map id:%s is missing [name]' % (layer.id, layer.map.id)
                pass
            else:
                config = json.loads(layer.layer_params)
                # do we need 'detail_url' ?
                attributes = ['title', 'url', 'selected', 'tiled', 'local', 'llbbox', 'detail_url']
                for attr in ['local', ]:
                    if not attr in config:
                        is_broken = True
                        print 'Layer id:%s in map id:%s is missing [%s]' % (layer.id, layer.map.id, attr)
        if is_broken:
            broken_wm_maps.append(map.id)
    return broken_wm_maps

def get_attributes_count():
    """
    Return a dictionary of attributes and count for all of the WM layers.
    """
    attributes = {}
    for map in Map.objects.all().order_by('id'):
        for layer in map.layer_set.filter(ows_url__icontains='worldmap.harvard.edu/geoserver/wms'):
            config = json.loads(layer.layer_params)
            for attr in config:
                if attr in attributes:
                    attributes[attr] += 1
                else:
                    attributes[attr] = 0
    return attributes

def fix_broken_snapshot(map_id):
    """
    Add local=True for all of the snapshots of a given map.
    """
    map = Map.objects.get(id=map_id)

    for ms in map.snapshot_set.all().order_by('created_dttm'):
        config = json.loads(ms.config)
        for layer in config['map']['layers']:
            if 'name' in layer:
                if layer['name'][:8] == 'geonode:':
                    layer['local'] = True
        new_config_s = json.dumps(config)
        ms.config = new_config_s
        ms.save()
