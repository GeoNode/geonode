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
import traceback

from django import forms
from django.conf import settings

from geonode.base.models import Thesaurus

from .widgets import MultiThesaurusWidget

logger = logging.getLogger(__name__)


class MultiThesauriField(forms.MultiValueField):

    widget = MultiThesaurusWidget()

    def __init__(self, *args, **kwargs):
        super(MultiThesauriField, self).__init__(*args, **kwargs)
        self.require_all_fields = kwargs.pop('require_all_fields', True)

        if hasattr(settings, 'THESAURUS') and settings.THESAURUS:
            el = settings.THESAURUS
            choices_list = []
            thesaurus_name = el['name']
            try:
                t = Thesaurus.objects.get(identifier=thesaurus_name)
                for tk in t.thesaurus.all():
                    tkl = tk.keyword.filter(lang='en')
                    choices_list.append((tkl[0].id, tkl[0].label))
                self.fields += (forms.MultipleChoiceField(choices=tuple(choices_list)), )
            except BaseException:
                tb = traceback.format_exc()
                logger.exception(tb)

        for f in self.fields:
            f.error_messages.setdefault('incomplete',
                                        self.error_messages['incomplete'])
            if self.require_all_fields:
                # Set 'required' to False on the individual fields, because the
                # required validation will be handled by MultiValueField, not
                # by those individual fields.
                f.required = False
