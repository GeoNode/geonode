# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
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
from django.utils.translation import ugettext as _

from geonode.base.models import TopicCategory


class CategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return '<span class="has-popover" data-container="body" data-toggle="popover" data-placement="top" ' \
               'data-content="' + obj.description + '" trigger="hover">' + obj.gn_description + '</span>'


class CategoryForm(forms.Form):
    category_choice_field = CategoryChoiceField(required=False,
                                                label='*' + _('Category'),
                                                empty_label=None,
                                                queryset=TopicCategory.objects.extra(order_by=['description']))

    def clean(self):
        cleaned_data = self.data
        ccf_data = cleaned_data.get("category_choice_field")

        if not ccf_data:
            msg = _("Category is required.")
            self._errors = self.error_class([msg])

        # Always return the full collection of cleaned data.
        return cleaned_data
