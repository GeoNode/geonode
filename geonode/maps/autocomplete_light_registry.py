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

from autocomplete_light.registry import register
from autocomplete_light.autocomplete.shortcuts import AutocompleteModelTemplate
from models import Map


class MapAutocomplete(AutocompleteModelTemplate):
    choice_template = 'autocomplete_response.html'


register(
    Map,
    MapAutocomplete,
    search_fields=['title'],
    order_by=['title'],
    limit_choices=100,
    autocomplete_js_attributes={
        'placeholder': 'Map name..',
    },
)
