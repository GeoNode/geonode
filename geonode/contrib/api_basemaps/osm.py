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

from geonode.settings import MAP_BASELAYERS
OSM = {
    'maps': {
        'de': {
            'enabled': True,
            'name': 'OSM DE',
            'visibility': False,
            'url': ('http://a.tile.openstreetmap.de/tiles/osmde/${z}/${x}/${y}'
                    '.png'),
            'attribution': ('&copy; <a href="http://www.openstreetmap.org/copy'
                            'right">OpenStreetMap</a>')
        },
        'france': {
            'enabled': True,
            'name': 'OSM France',
            'visibility': False,
            'url': ('http://a.tile.openstreetmap.fr/osmfr/${z}/${x}/${y}.png'),
            'attribution': ('&copy; Openstreetmap France | &copy; <a href="htt'
                            'p://www.openstreetmap.org/copyright">OpenStreetMa'
                            'p</a>')
        },
        'hot': {
            'enabled': True,
            'name': 'OSM HOT',
            'visibility': False,
            'url': ('http://a.tile.openstreetmap.fr/hot/${z}/${x}/${y}.png'),
            'attribution': ('&copy; <a href="http://www.openstreetmap.org/copy'
                            'right">OpenStreetMap</a>, Tiles courtesy of <a hr'
                            'ef="http://hot.openstreetmap.org/" target="_blank'
                            '">Humanitarian OpenStreetMap Team</a>')
        }
    }
}

for k, v in OSM['maps'].items():
    if v['enabled']:
        BASEMAP = {
            'source': {
                'ptype': 'gxp_olsource'
            },
            'type': 'OpenLayers.Layer.XYZ',
            "args": [
                '%s' % v['name'],
                [v['url']],
                {
                    'transitionEffect': 'resize',
                    'attribution': '%s' % v['attribution'],
                }
            ],
            'fixed': True,
            'visibility': v['visibility'],
            'group': 'background'
        }
        MAP_BASELAYERS.append(BASEMAP)
