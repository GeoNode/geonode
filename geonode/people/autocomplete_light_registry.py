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
from .models import Profile


class ProfileAutocomplete(AutocompleteModelTemplate):
    choice_template = 'autocomplete_response.html'

    def choices_for_request(self):
        self.choices = self.choices.exclude(username='AnonymousUser')
        return super(ProfileAutocomplete, self).choices_for_request()


register(
    Profile,
    ProfileAutocomplete,
    search_fields=['first_name', 'last_name', 'email', 'username'],
)
