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

from django.conf import settings
from autocomplete_light.widgets import MultipleChoiceWidget


class MultiThesaurusWidget(MultipleChoiceWidget):

    def __init__(self, attrs=None):
        if hasattr(settings, 'THESAURUS') and settings.THESAURUS:
            el = settings.THESAURUS
            widget_name = el['name']
            cleaned_name = el['name'].replace("-", " ").replace("_", " ").title()
            super(MultiThesaurusWidget, self).__init__(
                'thesaurus_' + widget_name,
                attrs={'placeholder': '%s - Start typing for suggestions' % cleaned_name},
                extra_context={'thesauri_title': cleaned_name})
        else:
            super(MultiThesaurusWidget, self).__init__([], attrs)
