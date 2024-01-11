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

register = template.Library()


@register.filter(is_safe=True)
def get_contact_role_id(form, contact):
    return id(form.fields[contact])


@register.filter(is_safe=True)
def get_contact_role_label(form, contact):
    return form.fields[contact].label


@register.filter(is_safe=True)
def get_contact_role_value(form, contact):
    return form[contact]


@register.simple_tag
def getattribute(form, contact):
    """Gets an attribute of an object dynamically from a string name"""
    return form[contact]
