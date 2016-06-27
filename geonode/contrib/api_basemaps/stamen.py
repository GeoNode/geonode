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
STAMEN = {
    'maps': {
        'toner': {
            'enabled': True,
            'name': 'Stamen Toner',
            'visibility': False,
        },
        'toner-lite': {
            'enabled': True,
            'name': 'Stamen Toner Lite',
            'visibility': False,
        },
        'watercolor': {
            'enabled': True,
            'name': 'Stamen Watercolor',
            'visibility': False,
        }
    }
}
ATTRIBUTION = ('Map tiles by <a href="http://stamen.com">Stamen Design</a>, <a'
               ' href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</'
               'a> &mdash; Map data &copy; <a href="http://www.openstreetmap.o'
               'rg/copyright">OpenStreetMap</a>')
for k, v in STAMEN['maps'].items():
    URL = 'http://stamen-tiles-a.a.ssl.fastly.net/%s/${z}/${x}/${y}.png' % k
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
