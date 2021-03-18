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

import json
import logging

from django.conf import settings

from .models import Map, MapLayer

logger = logging.getLogger(__name__)


def _layer_json(layers, sources):
    """
    return a list of layer config for the provided layer
    """
    server_lookup = {}

    def uniqify(seq):
        """
        get a list of unique items from the input sequence.

        This relies only on equality tests, so you can use it on most
        things.  If you have a sequence of hashables, list(set(seq)) is
        better.
        """
        results = []
        for x in seq:
            if x not in results:
                results.append(x)
        return results

    configs = [lyr.source_config() for lyr in layers]

    i = 0
    for source in uniqify(configs):
        while str(i) in sources:
            i = i + 1
        sources[str(i)] = source
        server_lookup[json.dumps(source)] = str(i)

    def source_lookup(source):
        for k, v in sources.items():
            if v == source:
                return k
        return None

    def layer_config(lyr, user=None):
        cfg = lyr.layer_config(user=user)
        src_cfg = lyr.source_config()
        source = source_lookup(src_cfg)
        if source:
            cfg["source"] = source
        return cfg

    return [layer_config(lyr, user=None) for lyr in layers]


def fix_baselayers(map_id):
    """
    Fix base layers for a given map.
    """

    try:
        id = int(map_id)
    except ValueError:
        logger.error('map_id must be an integer')
        return

    if not Map.objects.filter(pk=id).exists():
        logger.error(f'There is not a map with id {id}')
        return

    map = Map.objects.get(pk=id)
    # first we delete all of the base layers
    map.layer_set.filter(local=False).delete()

    # now we re-add them
    source = 0
    for base_layer in settings.MAP_BASELAYERS:
        if 'group' in base_layer:
            # layer_params
            layer_params = {}
            layer_params['selected'] = True
            if 'title' in base_layer:
                layer_params['title'] = base_layer['title']
            if 'type' in base_layer:
                layer_params['type'] = base_layer['type']
            if 'args' in base_layer:
                layer_params['args'] = base_layer['args']
            if 'wrapDateLine' in base_layer:
                layer_params['wrapDateLine'] = base_layer['wrapDateLine']
            else:
                layer_params['wrapDateLine'] = True
            # source_params
            source_params = {}
            source_params['id'] = source
            for param in base_layer['source']:
                source_params[param] = base_layer['source'][param]
            # let's create the map layer
            name = ''
            if 'name' in base_layer:
                name = base_layer['name']
            else:
                if 'args' in base_layer:
                    name = base_layer['args'][0]
            map_layer = MapLayer(
                map=map,
                stack_order=map.layer_set.count() + 1,
                name=name,
                opacity=1,
                transparent=False,
                fixed=True,
                group='background',
                layer_params=json.dumps(layer_params),
                source_params=json.dumps(source_params)
            )
            map_layer.save()
        source += 1
