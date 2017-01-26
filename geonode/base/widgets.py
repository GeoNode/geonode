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

from django import forms
from django.conf import settings

import autocomplete_light


class MultiThesauriWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        widget_list = []
        for el in settings.THESAURI:
            cleaned_name = el['name'].replace("-", " ").replace("_", " ").title()
            widget_list.append(
                autocomplete_light.MultipleChoiceWidget(
                    'thesaurus_' + el['name'],
                    attrs={'placeholder': '%s - Start typing for suggestions' % cleaned_name},
                    extra_context={'thesauri_title': cleaned_name}))
        widgets = tuple(widget_list)

        super(MultiThesauriWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [map(int, value.split(','))]
        return [None, None, None]

    def compress(self, data_list):
        if data_list:
            return '%s' % (data_list[0])
        return None

    def format_output(self, rendered_widgets):
        return u'\n'.join(rendered_widgets)
