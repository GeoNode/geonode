#########################################################################
#
# Copyright (C) 2018 OSGeo
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

from django import forms
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class TimeForm(forms.Form):
    presentation_strategy = forms.CharField(required=False)
    precision_value = forms.IntegerField(required=False)
    precision_step = forms.ChoiceField(
        required=False,
        choices=[("years",) * 2, ("months",) * 2, ("days",) * 2, ("hours",) * 2, ("minutes",) * 2, ("seconds",) * 2],
    )

    def __init__(self, *args, **kwargs):
        # have to remove these from kwargs or Form gets mad
        self._time_names = kwargs.pop("time_names", None)
        self._text_names = kwargs.pop("text_names", None)
        self._year_names = kwargs.pop("year_names", None)
        super().__init__(*args, **kwargs)
        self._build_choice("time_attribute", self._time_names)
        self._build_choice("end_time_attribute", self._time_names)
        self._build_choice("text_attribute", self._text_names)
        self._build_choice("end_text_attribute", self._text_names)
        widget = forms.TextInput(attrs={"placeholder": "Custom Format"})
        if self._text_names:
            self.fields["text_attribute_format"] = forms.CharField(required=False, widget=widget)
            self.fields["end_text_attribute_format"] = forms.CharField(required=False, widget=widget)
        self._build_choice("year_attribute", self._year_names)
        self._build_choice("end_year_attribute", self._year_names)

    def _resolve_attribute_and_type(self, *name_and_types):
        return [(self.cleaned_data[n], t) for n, t in name_and_types if self.cleaned_data.get(n, None)]

    def _build_choice(self, att, names):
        if names:
            names.sort()
            choices = [("", "<None>")] + [(a, a) for a in names]
            self.fields[att] = forms.ChoiceField(choices=choices, required=False)

    @property
    def time_names(self):
        return self._time_names

    @property
    def text_names(self):
        return self._text_names

    @property
    def year_names(self):
        return self._year_names

    def clean(self):
        starts = self._resolve_attribute_and_type(
            ("time_attribute", "Date"),
            ("text_attribute", "Text"),
            ("year_attribute", "Number"),
        )
        if len(starts) > 1:
            raise ValidationError("multiple start attributes")
        ends = self._resolve_attribute_and_type(
            ("end_time_attribute", "Date"),
            ("end_text_attribute", "Text"),
            ("end_year_attribute", "Number"),
        )
        if len(ends) > 1:
            raise ValidationError("multiple end attributes")
        if len(starts) > 0:
            self.cleaned_data["start_attribute"] = starts[0]
        if len(ends) > 0:
            self.cleaned_data["end_attribute"] = ends[0]
        return self.cleaned_data

    # @todo implement clean
