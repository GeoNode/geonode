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
CARTODB = {
    'maps': {
        'light_all': {
            'enabled': True,
            'name': 'CartoDB Positron',
            'visibility': False,
        },
        'dark_all': {
            'enabled': True,
            'name': 'CartoDB Dark Matter',
            'visibility': False,
        }
    }
}
ATTRIBUTION = ('&copy; <a href="http://www.openstreetmap.org/copyright">OpenSt'
               'reetMap</a> contributors, &copy; <a href="http://cartodb.com/a'
               'ttributions">CartoDB</a>')
for k, v in CARTODB['maps'].items():
    URL = 'https://s.basemaps.cartocdn.com/%s/${z}/${x}/${y}.png' % k
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
                    'attribution': '%s' % ATTRIBUTION,
                }
            ],
            'fixed': True,
            'visibility': v['visibility'],
            'group': 'background'
        }
        MAP_BASELAYERS.append(BASEMAP)
