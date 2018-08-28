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

import logging

from autocomplete_light.registry import register
from autocomplete_light.autocomplete.shortcuts import AutocompleteModelBase, AutocompleteModelTemplate

from guardian.shortcuts import get_objects_for_user
from django.conf import settings
from django.db.models import Q
from geonode.security.utils import get_visible_resources

from models import ResourceBase, Region, HierarchicalKeyword, ThesaurusKeywordLabel

logger = logging.getLogger(__name__)


class ResourceBaseAutocomplete(AutocompleteModelTemplate):
    choice_template = 'autocomplete_response.html'
    model = ResourceBase

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

        return super(ResourceBaseAutocomplete, self).choices_for_request()


register(Region,
         search_fields=['name'],
         autocomplete_js_attributes={'placeholder': 'Region/Country ..', },)

register(ResourceBaseAutocomplete,
         search_fields=['title'],
         order_by=['title'],
         limit_choices=100,
         autocomplete_js_attributes={'placeholder': 'Resource name..', },)

register(HierarchicalKeyword,
         search_fields=['name', 'slug'],
         autocomplete_js_attributes={'placeholder':
                                     'A space or comma-separated list of keywords', },)


class ThesaurusKeywordLabelAutocomplete(AutocompleteModelBase):

    search_fields = ['label']

    model = ThesaurusKeywordLabel

    def choices_for_request(self):

        lang = 'en'  # TODO: use user's language
        self.choices = self.choices.filter(lang=lang)
        return super(ThesaurusKeywordLabelAutocomplete, self).choices_for_request()


if hasattr(settings, 'THESAURI'):
    for thesaurus in settings.THESAURI:

        tname = thesaurus['name']
        ac_name = 'thesaurus_' + tname

        logger.debug('Registering thesaurus autocomplete for {}: {}'.format(tname, ac_name))

        register(
            ThesaurusKeywordLabelAutocomplete,
            name=ac_name,
            choices=ThesaurusKeywordLabel.objects.filter(Q(keyword__thesaurus__identifier=tname))
        )
