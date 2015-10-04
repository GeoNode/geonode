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
import os
import files
import tempfile
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from geonode.layers.forms import JSONField
from geonode.upload.models import UploadFile
from geonode.geoserver.helpers import ogc_server_settings


class UploadFileForm(forms.ModelForm):

    class Meta:
        model = UploadFile


class LayerUploadForm(forms.Form):
    base_file = forms.FileField()
    dbf_file = forms.FileField(required=False)
    shx_file = forms.FileField(required=False)
    prj_file = forms.FileField(required=False)
    sld_file = forms.FileField(required=False)
    xml_file = forms.FileField(required=False)

    geogig = forms.BooleanField(required=False)
    geogig_store = forms.CharField(required=False)
    time = forms.BooleanField(required=False)

    abstract = forms.CharField(required=False)
    layer_title = forms.CharField(required=False)
    permissions = JSONField()

    spatial_files = (
        "base_file",
        "dbf_file",
        "shx_file",
        "prj_file",
        "sld_file",
        "xml_file")

    def clean(self):
        requires_datastore = () if ogc_server_settings.DATASTORE else (
            '.csv',
            '.kml')
        types = [t for t in files.types if t.code not in requires_datastore]

        def supported_type(ext):
            return any([t.matches(ext) for t in types])

        cleaned = super(LayerUploadForm, self).clean()
        base_name, base_ext = os.path.splitext(cleaned["base_file"].name)
        if base_ext.lower() == '.zip':
            # for now, no verification, but this could be unified
            pass
        elif not supported_type(base_ext.lower()[1:]):
            supported = " , ".join([t.name for t in types])
            raise forms.ValidationError(
                "%s files are supported. You uploaded a %s file" %
                (supported, base_ext))
        if base_ext.lower() == ".shp":
            dbf_file = cleaned["dbf_file"]
            shx_file = cleaned["shx_file"]
            if dbf_file is None or shx_file is None:
                raise forms.ValidationError(
                    "When uploading Shapefiles, .SHX and .DBF files are also required.")
            dbf_name, __ = os.path.splitext(dbf_file.name)
            shx_name, __ = os.path.splitext(shx_file.name)
            if dbf_name != base_name or shx_name != base_name:
                raise forms.ValidationError(
                    "It looks like you're uploading "
                    "components from different Shapefiles. Please "
                    "double-check your file selections.")
            if cleaned["prj_file"] is not None:
                prj_file = cleaned["prj_file"].name
                if os.path.splitext(prj_file)[0] != base_name:
                    raise forms.ValidationError(
                        "It looks like you're "
                        "uploading components from different Shapefiles. "
                        "Please double-check your file selections.")
        return cleaned

    def write_files(self):
        tempdir = tempfile.mkdtemp(dir=settings.FILE_UPLOAD_TEMP_DIR)
        for field in self.spatial_files:
            f = self.cleaned_data[field]
            if f is not None:
                path = os.path.join(tempdir, f.name)
                with open(path, 'wb') as writable:
                    for c in f.chunks():
                        writable.write(c)
        absolute_base_file = os.path.join(tempdir,
                                          self.cleaned_data["base_file"].name)
        return tempdir, absolute_base_file


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
        time_names = kwargs.pop('time_names', None)
        text_names = kwargs.pop('text_names', None)
        year_names = kwargs.pop('year_names', None)
        super(TimeForm, self).__init__(*args, **kwargs)
        self._build_choice('time_attribute', time_names)
        self._build_choice('end_time_attribute', time_names)
        self._build_choice('text_attribute', text_names)
        self._build_choice('end_text_attribute', text_names)
        widget = forms.TextInput(attrs={'placeholder': 'Custom Format'})
        if text_names:
            self.fields['text_attribute_format'] = forms.CharField(
                required=False, widget=widget)
            self.fields['end_text_attribute_format'] = forms.CharField(
                required=False, widget=widget)
        self._build_choice('year_attribute', year_names)
        self._build_choice('end_year_attribute', year_names)

    def _resolve_attribute_and_type(self, *name_and_types):
        return [(self.cleaned_data[n], t) for n, t in name_and_types
                if self.cleaned_data.get(n, None)]

    def _build_choice(self, att, names):
        if names:
            names.sort()
            choices = [('', '<None>')] + [(a, a) for a in names]
            self.fields[att] = forms.ChoiceField(
                choices=choices, required=False)

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
    srs = forms.CharField(required=True)
