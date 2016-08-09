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

from geonode.settings import MAP_BASELAYERS, MAPBOX_ACCESS_TOKEN
MAPBOX_API = {
    'styles': {
        'streets-v9': {
            'enabled': True,
            'name': 'Mapbox Streetmap',
            'attribution': '© Mapbox © OpenStreetMap',
            'visibility': False,
        },
        'outdoors-v9': {
            'enabled': True,
            'name': 'Mapbox Outdoors',
            'attribution': '© Mapbox © OpenStreetMap',
            'visibility': False,
        },
        'dark-v9': {
            'enabled': True,
            'name': 'Mapbox Dark',
            'attribution': '© Mapbox © OpenStreetMap',
            'visibility': False,
        },
        'light-v9': {
            'enabled': True,
            'name': 'Mapbox Light',
            'attribution': '© Mapbox © OpenStreetMap',
            'visibility': False,
        },
        'satellite-v9': {
            'enabled': True,
            'name': 'Mapbox Satellite',
            'attribution': '© Mapbox © DigitalGlobe',
            'visibility': False,
        },
        'satellite-streets-v9': {
            'enabled': True,
            'name': 'Mapbox Satellite Streets',
            'attribution': '© Mapbox © OpenStreetMap © DigitalGlobe',
            'visibility': False,
        },
    }
}

for k, v in MAPBOX_API['styles'].items():
    URL = ('https://api.mapbox.com/styles/v1/mapbox/%s/tiles/256/${z}/${x}/'
           '${y}?access_token=%s') % (k, MAPBOX_ACCESS_TOKEN)
    if v['enabled']:
        BASEMAP = {
            'source': {
                'ptype': 'gxp_olsource'
            },
            'type': 'OpenLayers.Layer.XYZ',
            "args": [
                '%s' % v['name'],
                [URL],
                {
                    'transitionEffect': 'resize',
                    'attribution': '%s' % v['attribution']
                }
            ],
            'fixed': True,
            'visibility': v['visibility'],
            'group': 'background'
        }
        MAP_BASELAYERS.append(BASEMAP)
