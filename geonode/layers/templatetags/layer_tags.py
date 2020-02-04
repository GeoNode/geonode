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
from django.conf import settings
from inflection import camelize as do_camelize

register = template.Library()


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
    if value in settings.EPSG_CODE_MATCHES.keys():
        return settings.EPSG_CODE_MATCHES[value]
    return value
