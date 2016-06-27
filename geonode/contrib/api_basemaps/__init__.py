# flake8: noqa
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

from geonode.settings import (
    ALT_OSM_BASEMAPS,
    CARTODB_BASEMAPS,
    STAMEN_BASEMAPS,
    THUNDERFOREST_BASEMAPS,
    MAPBOX_ACCESS_TOKEN,
    BING_API_KEY,
)

if ALT_OSM_BASEMAPS:
    try:
        from osm import *
    except ImportError:
        pass

if CARTODB_BASEMAPS:
    try:
        from cartodb import *
    except ImportError:
        pass

if STAMEN_BASEMAPS:
    try:
        from stamen import *
    except ImportError:
        pass

if THUNDERFOREST_BASEMAPS:
    try:
        from thunderforest import *
    except ImportError:
        pass

if BING_API_KEY is not None:
    try:
        from bing import *
    except ImportError:
        pass

if MAPBOX_ACCESS_TOKEN is not None:
    try:
        from mapbox import *
    except ImportError:
        pass
