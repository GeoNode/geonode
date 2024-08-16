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

import json
from geonode.base.forms import ResourceBaseForm, get_tree_data
from geonode.layers.models import Dataset, Attribute


class JSONField(forms.CharField):
    def clean(self, text):
        text = super().clean(text)

        if not self.required and (text is None or text == ""):
            return None

        try:
            return json.loads(text)
        except ValueError:
            raise forms.ValidationError("this field must be valid JSON")


class DatasetForm(ResourceBaseForm):
    class Meta(ResourceBaseForm.Meta):
        model = Dataset
        exclude = ResourceBaseForm.Meta.exclude + (
            "store",
            "styles",
            "subtype",
            "alternate",
            "workspace",
            "default_style",
            "upload_session",
            "resource_type",
            "remote_service",
            "remote_typename",
            "users_geolimits",
            "groups_geolimits",
            "blob",
            "files",
            "ows_url",
        )
        # widgets = {
        #     'title': forms.TextInput({'placeholder': title_help_text})
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["regions"].choices = get_tree_data()
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != "":
                self.fields[field].widget.attrs.update(
                    {
                        "class": "has-external-popover",
                        "data-content": help_text,
                        "placeholder": help_text,
                        "data-placement": "right",
                        "data-container": "body",
                        "data-html": "true",
                    }
                )


class LayerDescriptionForm(forms.Form):
    title = forms.CharField(max_length=300, required=True)
    abstract = forms.CharField(max_length=2000, widget=forms.Textarea, required=False)
    supplemental_information = forms.CharField(max_length=2000, widget=forms.Textarea, required=False)
    data_quality_statement = forms.CharField(max_length=2000, widget=forms.Textarea, required=False)
    purpose = forms.CharField(max_length=500, required=False)
    keywords = forms.CharField(max_length=500, required=False)


class LayerAttributeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["attribute"].widget.attrs["readonly"] = True
        self.fields["display_order"].widget.attrs["size"] = 3

    class Meta:
        model = Attribute
        exclude = (
            "attribute_type",
            "count",
            "min",
            "max",
            "average",
            "median",
            "stddev",
            "sum",
            "unique_values",
            "last_stats_updated",
            "objects",
        )


class DatasetTimeSerieForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        _choises = [(None, "-----")] + [
            (_a.pk, _a.attribute)
            for _a in kwargs.get("instance").attributes
            if _a.attribute_type in ["xsd:dateTime", "xsd:date"]
        ]
        self.base_fields.get("attribute").choices = _choises
        self.base_fields.get("end_attribute").choices = _choises
        super().__init__(*args, **kwargs)

    class Meta:
        model = Attribute
        fields = ("attribute",)

    attribute = forms.ChoiceField(
        required=False,
    )
    end_attribute = forms.ChoiceField(
        required=False,
    )
    presentation = forms.ChoiceField(
        required=False,
        choices=[
            ("LIST", "List of all the distinct time values"),
            ("DISCRETE_INTERVAL", "Intervals defined by the resolution"),
            (
                "CONTINUOUS_INTERVAL",
                "Continuous Intervals for data that is frequently updated, resolution describes the frequency of updates",
            ),
        ],
    )
    precision_value = forms.IntegerField(required=False)
    precision_step = forms.ChoiceField(
        required=False,
        choices=[("years",) * 2, ("months",) * 2, ("days",) * 2, ("hours",) * 2, ("minutes",) * 2, ("seconds",) * 2],
    )
