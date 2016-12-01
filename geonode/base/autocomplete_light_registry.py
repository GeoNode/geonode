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

import autocomplete_light

from models import ResourceBase, Region, HierarchicalKeyword
from guardian.shortcuts import get_objects_for_user


class ResourceBaseAutocomplete(autocomplete_light.AutocompleteModelTemplate):
    choice_template = 'autocomplete_response.html'
    model = ResourceBase

    def choices_for_request(self):
        permitted = get_objects_for_user(
            self.request.user,
            'base.view_resourcebase')
        self.choices = self.choices.filter(id__in=permitted)

        return super(ResourceBaseAutocomplete, self).choices_for_request()


autocomplete_light.register(Region,
                            search_fields=['name'],
                            autocomplete_js_attributes={'placeholder': 'Region/Country ..', },)

autocomplete_light.register(ResourceBaseAutocomplete,
                            search_fields=['title'],
                            order_by=['title'],
                            limit_choices=100,
                            autocomplete_js_attributes={'placeholder': 'Resource name..', },)

autocomplete_light.register(HierarchicalKeyword,
                            search_fields=['name', 'slug'],
                            autocomplete_js_attributes={'placeholder':
                                                        'A space or comma-separated list of keywords', },)
