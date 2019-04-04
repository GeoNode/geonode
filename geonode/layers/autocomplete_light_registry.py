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
from models import Layer
from guardian.shortcuts import get_objects_for_user

from django.conf import settings
from geonode.security.utils import get_visible_resources


class LayerAutocomplete(AutocompleteModelTemplate):
    choice_template = 'autocomplete_response.html'

    def choices_for_request(self):
        request = self.request
        permitted = get_objects_for_user(
            request.user,
            'base.view_resourcebase')
        self.choices = self.choices.filter(id__in=permitted)

        self.choices = get_visible_resources(
            self.choices,
            request.user if request else None,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)

        return super(LayerAutocomplete, self).choices_for_request()


register(
    Layer,
    LayerAutocomplete,
    search_fields=[
        'title',
        '^alternate'],
    order_by=['title'],
    limit_choices=100,
    autocomplete_js_attributes={
        'placeholder': 'Layer name..',
    },
)
