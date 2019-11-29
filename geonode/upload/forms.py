# -*- coding: utf-8 -*-
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

from .. import geoserver
from .. import qgis_server
from ..utils import check_ogc_backend
from ..layers.forms import JSONField

from .models import UploadFile
from .upload_validators import validate_uploaded_files

logger = logging.getLogger(__name__)


class UploadFileForm(forms.ModelForm):

    class Meta:
        model = UploadFile
        fields = '__all__'


class LayerUploadForm(forms.Form):
    base_file = forms.FileField()
    dbf_file = forms.FileField(required=False)
    shx_file = forms.FileField(required=False)
    prj_file = forms.FileField(required=False)
    xml_file = forms.FileField(required=False)
    charset = forms.CharField(required=False)

    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        sld_file = forms.FileField(required=False)
    if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
        qml_file = forms.FileField(required=False)

    time = forms.BooleanField(required=False)

    mosaic = forms.BooleanField(required=False)
    append_to_mosaic_opts = forms.BooleanField(required=False)
    append_to_mosaic_name = forms.CharField(required=False)
    mosaic_time_regex = forms.CharField(required=False)
    mosaic_time_value = forms.CharField(required=False)
    time_presentation = forms.CharField(required=False)
    time_presentation_res = forms.IntegerField(required=False)
    time_presentation_default_value = forms.CharField(required=False)
    time_presentation_reference_value = forms.CharField(required=False)

    abstract = forms.CharField(required=False)
    layer_title = forms.CharField(required=False)
    permissions = JSONField()

    metadata_uploaded_preserve = forms.BooleanField(required=False)
    metadata_upload_form = forms.BooleanField(required=False)
    style_upload_form = forms.BooleanField(required=False)

    spatial_files = [
        "base_file",
        "dbf_file",
        "shx_file",
        "prj_file",
        "xml_file",
    ]
    # Adding style file based on the backend
    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        spatial_files.append('sld_file')
    if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
        spatial_files.append('qml_file')

    spatial_files = tuple(spatial_files)

    def clean(self):
        cleaned = super(LayerUploadForm, self).clean()
        uploaded_files = self._get_uploaded_files()
        valid_extensions = validate_uploaded_files(
            cleaned=cleaned,
            uploaded_files=uploaded_files,
            field_spatial_types=self.spatial_files
        )
        cleaned["valid_extensions"] = valid_extensions
        return cleaned

    def _get_uploaded_files(self):
        """Return a list with all of the uploaded files"""
        return [django_file for field_name, django_file in self.files.items()
                if field_name != "base_file"]


class TimeForm(forms.Form):
    presentation_strategy = forms.CharField(required=False)
    precision_value = forms.IntegerField(required=False)
    precision_step = forms.ChoiceField(required=False, choices=[
        ('years',) * 2,
        ('months',) * 2,
        ('days',) * 2,
        ('hours',) * 2,
        ('minutes',) * 2,
        ('seconds',) * 2
    ])

    def __init__(self, *args, **kwargs):
        # have to remove these from kwargs or Form gets mad
        self._time_names = kwargs.pop('time_names', None)
        self._text_names = kwargs.pop('text_names', None)
        self._year_names = kwargs.pop('year_names', None)
        super(TimeForm, self).__init__(*args, **kwargs)
        self._build_choice('time_attribute', self._time_names)
        self._build_choice('end_time_attribute', self._time_names)
        self._build_choice('text_attribute', self._text_names)
        self._build_choice('end_text_attribute', self._text_names)
        widget = forms.TextInput(attrs={'placeholder': 'Custom Format'})
        if self._text_names:
            self.fields['text_attribute_format'] = forms.CharField(
                required=False, widget=widget)
            self.fields['end_text_attribute_format'] = forms.CharField(
                required=False, widget=widget)
        self._build_choice('year_attribute', self._year_names)
        self._build_choice('end_year_attribute', self._year_names)

    def _resolve_attribute_and_type(self, *name_and_types):
        return [(self.cleaned_data[n], t) for n, t in name_and_types
                if self.cleaned_data.get(n, None)]

    def _build_choice(self, att, names):
        if names:
            names.sort()
            choices = [('', '<None>')] + [(a, a) for a in names]
            self.fields[att] = forms.ChoiceField(
                choices=choices, required=False)

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
            ('time_attribute', 'Date'),
            ('text_attribute', 'Text'),
            ('year_attribute', 'Number'),
        )
        if len(starts) > 1:
            raise ValidationError('multiple start attributes')
        ends = self._resolve_attribute_and_type(
            ('end_time_attribute', 'Date'),
            ('end_text_attribute', 'Text'),
            ('end_year_attribute', 'Number'),
        )
        if len(ends) > 1:
            raise ValidationError('multiple end attributes')
        if len(starts) > 0:
            self.cleaned_data['start_attribute'] = starts[0]
        if len(ends) > 0:
            self.cleaned_data['end_attribute'] = ends[0]
        return self.cleaned_data

    # @todo implement clean


class SRSForm(forms.Form):
    source = forms.CharField(required=True)

    target = forms.CharField(required=False)


def _supported_type(ext, supported_types):
    return any([type_.matches(ext) for type_ in supported_types])
