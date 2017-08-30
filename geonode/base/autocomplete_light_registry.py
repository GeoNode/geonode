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

from guardian.shortcuts import get_objects_for_user
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import Group

from models import ResourceBase, Region, HierarchicalKeyword, ThesaurusKeywordLabel


class ResourceBaseAutocomplete(autocomplete_light.AutocompleteModelTemplate):
    choice_template = 'autocomplete_response.html'
    model = ResourceBase

    def choices_for_request(self):
        request = self.request
        permitted = get_objects_for_user(
            request.user,
            'base.view_resourcebase')
        self.choices = self.choices.filter(id__in=permitted)

        is_admin = False
        is_staff = False
        if request.user:
            is_admin = request.user.is_superuser if request.user else False
            is_staff = request.user.is_staff if request.user else False

        if settings.ADMIN_MODERATE_UPLOADS:
            if not is_admin and not is_staff:
                self.choices = self.choices.filter(is_published=True)

        if settings.RESOURCE_PUBLISHING:
            self.choices = self.choices.filter(is_published=True)

        try:
            anonymous_group = Group.objects.get(name='anonymous')
        except:
            anonymous_group = None

        if settings.GROUP_PRIVATE_RESOURCES:
            if is_admin:
                self.choices = self.choices
            elif request.user:
                groups = request.user.groups.all()
                if anonymous_group:
                    self.choices = self.choices.filter(
                        Q(group__isnull=True) | Q(group__in=groups) | Q(group=anonymous_group))
                else:
                    self.choices = self.choices.filter(Q(group__isnull=True) | Q(group__in=groups))
            else:
                if anonymous_group:
                    self.choices = self.choices.filter(Q(group__isnull=True) | Q(group=anonymous_group))
                else:
                    self.choices = self.choices.filter(Q(group__isnull=True))

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


class ThesaurusKeywordLabelAutocomplete(autocomplete_light.AutocompleteModelBase):

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

        # print('Registering thesaurus autocomplete for {}: {}'.format(tname, ac_name))

        autocomplete_light.register(
            ThesaurusKeywordLabelAutocomplete,
            name=ac_name,
            choices=ThesaurusKeywordLabel.objects.filter(Q(keyword__thesaurus__identifier=tname))
        )
