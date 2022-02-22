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
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

from geonode.upload.models import UploadSizeLimit
from geonode.upload.data_retriever import DataRetriever

from .. import geoserver
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
    base_file = forms.FileField(required=False)
    base_file_path = forms.CharField(required=False)
    dbf_file = forms.FileField(required=False)
    dbf_file_path = forms.CharField(required=False)
    shx_file = forms.FileField(required=False)
    shx_file_path = forms.CharField(required=False)
    prj_file = forms.FileField(required=False)
    prj_file_path = forms.CharField(required=False)
    xml_file = forms.FileField(required=False)
    xml_file_path = forms.CharField(required=False)
    charset = forms.CharField(required=False)

    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        sld_file = forms.FileField(required=False)
        sld_file_path = forms.CharField(required=False)

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
    permissions = JSONField(required=False)

    metadata_uploaded_preserve = forms.BooleanField(required=False)
    metadata_upload_form = forms.BooleanField(required=False)
    style_upload_form = forms.BooleanField(required=False)

    store_spatial_files = forms.BooleanField(required=False, initial=True)

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

    spatial_files = tuple(spatial_files)

    def clean(self):
        cleaned = super().clean()
        uploaded, files = self._get_files_paths_or_objects(cleaned)
        cleaned["uploaded"] = uploaded
        base_file = files.get('base_file')

        if not base_file and "base_file" not in self.errors and "base_file_path" not in self.errors:
            logger.error("Base file must be a file or url.")
            raise ValidationError(_("Base file must be a file or url."))

        if self.errors:
            # Something already went wrong
            return cleaned

        # Validate form file sizes
        self.validate_files_sum_of_sizes(self.files)

        # Get remote files
        self.data_retriever = DataRetriever(files=files, tranfer_at_creation=True)
        cleaned["data_retriever"] = self.data_retriever
        # Validate remote file sizes
        self.validate_files_sum_of_sizes(self.data_retriever)

        file_paths_without_base = self.data_retriever.get_paths()
        base_file_path = file_paths_without_base.pop("base_file")

        valid_extensions = validate_uploaded_files(
            cleaned=cleaned,
            uploaded_files=file_paths_without_base,
            field_spatial_types=self.spatial_files,
            base_file_path=base_file_path,
        )
        cleaned["valid_extensions"] = valid_extensions
        return cleaned

    def _get_files_paths_or_objects(self, cleaned_data):
        """Return a dict with all of the uploaded files"""
        files = {}
        uploaded = True
        file_fields = (
            ("base_file", "base_file_path"),
            ("dbf_file", "dbf_file_path"),
            ("shx_file", "shx_file_path"),
            ("prj_file", "prj_file_path"),
            ("xml_file", "xml_file_path"),
            ("sld_file", "sld_file_path")
        )
        for file_field in file_fields:
            field_name = file_field[0]
            file_field_value = cleaned_data.get(file_field[0], None)
            path_field_value = cleaned_data.get(file_field[1], None)
            if file_field_value and path_field_value:
                raise ValidationError(_(
                    f"`{field_name}` field cannot have both a file and a path. Please choose one and try again."
                ))
            if path_field_value:
                uploaded = False
                files[field_name] = path_field_value
            elif file_field_value:
                uploaded = True
                files[field_name] = file_field_value

        return uploaded, files

    def validate_files_sum_of_sizes(self, file_dict):
        max_size = self._get_uploads_max_size()
        total_size = self._get_uploaded_files_total_size(file_dict)
        if total_size > max_size:
            raise ValidationError(_(
                f'Total upload size exceeds {filesizeformat(max_size)}. Please try again with smaller files.'
            ))

    def _get_uploads_max_size(self):
        try:
            max_size_db_obj = UploadSizeLimit.objects.get(slug="total_upload_size_sum")
        except UploadSizeLimit.DoesNotExist:
            max_size_db_obj = UploadSizeLimit.objects.create_default_limit()
        return max_size_db_obj.max_size

    def _get_uploaded_files(self):
        """Return a list with all of the uploaded files"""
        return [django_file for field_name, django_file in self.files.items()
                if field_name != "base_file"]

    def _get_uploaded_files_total_size(self, file_dict):
        """Return a list with all of the uploaded files"""
        excluded_files = ("zip_file", "shp_file", )
        uploaded_files_sizes = [
            file_obj.size for field_name, file_obj in file_dict.items()
            if field_name not in excluded_files
        ]
        total_size = sum(uploaded_files_sizes)
        return total_size


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
        super().__init__(*args, **kwargs)
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
