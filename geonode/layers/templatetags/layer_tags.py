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

from django import template
from inflection import camelize as do_camelize

register = template.Library()

EPSG_CODE_MATCHES = {
    'EPSG:4326': '(4326) WGS 84',
    'EPSG:900913': '(900913) Google Maps Global Mercator',
    'EPSG:3857': '(3857) WGS 84 / Pseudo-Mercator',
    'EPSG:3785': '(3785 DEPRECATED) Popular Visualisation CRS / Mercator',
    'EPSG:32647': '(32647) WGS 84 / UTM zone 47N',
    'EPSG:32736': '(32736) WGS 84 / UTM zone 36S'
}


@register.filter(is_safe=True)
def lower(value):  # Only one argument.
    """Converts a string into all lowercase"""
    return value.lower()


@register.filter(is_safe=True)
def camelize(value):  # Only one argument.
    if str(value)[0].isdigit():
        return value
    else:
        """Converts a string into all camel"""
        return do_camelize(value)


@register.filter(is_safe=True)
def crs_labels(value):  # Only one argument.
    """Converts a EPSG SRS ID into a human readable string"""
    if value in EPSG_CODE_MATCHES.keys():
        return EPSG_CODE_MATCHES[value]
    return value
