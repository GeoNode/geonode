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
import os
import zipfile

from django import forms

from geonode import geoserver
from geonode.utils import check_ogc_backend

import json
from geonode.utils import unzip_file, mkdtemp
from geonode.base.forms import ResourceBaseForm, get_tree_data
from geonode.layers.models import Dataset, Attribute


class JSONField(forms.CharField):

    def clean(self, text):
        text = super().clean(text)

        if not self.required and (text is None or text == ''):
            return None

        try:
            return json.loads(text)
        except ValueError:
            raise forms.ValidationError("this field must be valid JSON")


class DatasetForm(ResourceBaseForm):

    class Meta(ResourceBaseForm.Meta):
        model = Dataset
        exclude = ResourceBaseForm.Meta.exclude + (
            'store',
            'styles',
            'subtype',
            'alternate',
            'workspace',
            'default_style',
            'upload_session',
            'resource_type',
            'remote_service',
            'remote_typename',
            'users_geolimits',
            'groups_geolimits',
            'blob',
            'files',
            'ows_url'
        )
        # widgets = {
        #     'title': forms.TextInput({'placeholder': title_help_text})
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['regions'].choices = get_tree_data()
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update(
                    {
                        'class': 'has-external-popover',
                        'data-content': help_text,
                        'placeholder': help_text,
                        'data-placement': 'right',
                        'data-container': 'body',
                        'data-html': 'true'
                    }
                )


class LayerUploadForm(forms.Form):
    base_file = forms.FileField()
    dbf_file = forms.FileField(required=False)
    shx_file = forms.FileField(required=False)
    prj_file = forms.FileField(required=False)
    xml_file = forms.FileField(required=False)
    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        sld_file = forms.FileField(required=False)

    charset = forms.CharField(required=False)
    metadata_uploaded_preserve = forms.BooleanField(required=False)
    metadata_upload_form = forms.BooleanField(required=False)
    style_upload_form = forms.BooleanField(required=False)

    spatial_files = [
        "base_file",
        "dbf_file",
        "shx_file",
        "prj_file"]

    # Adding style file based on the backend
    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        spatial_files.append('sld_file')

    spatial_files = tuple(spatial_files)

    def clean(self):
        cleaned = super().clean()
        dbf_file = shx_file = prj_file = xml_file = sld_file = None
        base_name = base_ext = None
        if zipfile.is_zipfile(cleaned["base_file"]):
            filenames = zipfile.ZipFile(cleaned["base_file"], allowZip64=True).namelist()
            for filename in filenames:
                name, ext = os.path.splitext(filename)
                if ext.lower() == '.shp':
                    if base_name is not None:
                        raise forms.ValidationError(
                            "Only one shapefile per zip is allowed")
                    base_name = name
                    base_ext = ext
                elif ext.lower() == '.dbf':
                    dbf_file = filename
                elif ext.lower() == '.shx':
                    shx_file = filename
                elif ext.lower() == '.prj':
                    prj_file = filename
                elif ext.lower() == '.xml':
                    xml_file = filename
                elif ext.lower() == '.sld':
                    sld_file = filename
            if base_name is None:
                raise forms.ValidationError(
                    "Zip files can only contain shapefile.")
        else:
            base_name, base_ext = os.path.splitext(cleaned["base_file"].name)
            if cleaned["dbf_file"] is not None:
                dbf_file = cleaned["dbf_file"].name
            if cleaned["shx_file"] is not None:
                shx_file = cleaned["shx_file"].name
            if cleaned["prj_file"] is not None:
                prj_file = cleaned["prj_file"].name
            if cleaned["xml_file"] is not None:
                xml_file = cleaned["xml_file"].name
            # SLD style only available in GeoServer backend
            if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                if cleaned["sld_file"] is not None:
                    sld_file = cleaned["sld_file"].name

        if not cleaned["metadata_upload_form"] and not cleaned["style_upload_form"] and base_ext.lower() not in (
                ".shp", ".tif", ".tiff", ".geotif", ".geotiff", ".asc", ".sld", ".kml", ".kmz", ".csv"):
            raise forms.ValidationError(
                f"Only Shapefiles, GeoTiffs, and ASCIIs are supported. You uploaded a {base_ext} file")
        elif cleaned["metadata_upload_form"] and base_ext.lower() not in (".xml"):
            raise forms.ValidationError(
                f"Only XML files are supported. You uploaded a {base_ext} file")
        elif cleaned["style_upload_form"] and base_ext.lower() not in (".sld"):
            raise forms.ValidationError(
                f"Only SLD files are supported. You uploaded a {base_ext} file")

        if base_ext.lower() == ".shp":
            if dbf_file is None or shx_file is None:
                raise forms.ValidationError(
                    "When uploading Shapefiles, .shx and .dbf files are also required.")
            dbf_name, __ = os.path.splitext(dbf_file)
            shx_name, __ = os.path.splitext(shx_file)
            if dbf_name != base_name or shx_name != base_name:
                raise forms.ValidationError(
                    "It looks like you're uploading "
                    "components from different Shapefiles. Please "
                    "double-check your file selections.")
            if prj_file is not None:
                if os.path.splitext(prj_file)[0] != base_name:
                    raise forms.ValidationError(
                        "It looks like you're "
                        "uploading components from different Shapefiles. "
                        "Please double-check your file selections.")
            if xml_file is not None:
                if os.path.splitext(xml_file)[0] != base_name:
                    if xml_file.find('.shp') != -1:
                        # force rename of file so that file.shp.xml doesn't
                        # overwrite as file.shp
                        if cleaned.get("xml_file"):
                            cleaned["xml_file"].name = f'{base_name}.xml'
            if sld_file is not None:
                if os.path.splitext(sld_file)[0] != base_name:
                    if sld_file.find('.shp') != -1:
                        # force rename of file so that file.shp.xml doesn't
                        # overwrite as file.shp
                        if cleaned.get("sld_file"):
                            cleaned["sld_file"].name = f'{base_name}.sld'
        return cleaned

    def write_files(self):
        absolute_base_file = None
        tempdir = mkdtemp()
        if zipfile.is_zipfile(self.cleaned_data['base_file']):
            absolute_base_file = unzip_file(self.cleaned_data['base_file'],
                                            '.shp', tempdir=tempdir)
        else:
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


class NewLayerUploadForm(LayerUploadForm):
    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        sld_file = forms.FileField(required=False)
    xml_file = forms.FileField(required=False)

    abstract = forms.CharField(required=False)
    dataset_title = forms.CharField(required=False)
    permissions = JSONField()
    charset = forms.CharField(required=False)
    metadata_uploaded_preserve = forms.BooleanField(required=False)

    spatial_files = [
        "base_file",
        "dbf_file",
        "shx_file",
        "prj_file",
        "xml_file"
    ]
    # Adding style file based on the backend
    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        spatial_files.append('sld_file')

    spatial_files = tuple(spatial_files)


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
        self.fields['attribute'].widget.attrs['readonly'] = True
        self.fields['display_order'].widget.attrs['size'] = 3

    class Meta:
        model = Attribute
        exclude = (
            'attribute_type',
            'count',
            'min',
            'max',
            'average',
            'median',
            'stddev',
            'sum',
            'unique_values',
            'last_stats_updated',
            'objects')


class LayerStyleUploadForm(forms.Form):
    layerid = forms.IntegerField()
    name = forms.CharField(required=False)
    update = forms.BooleanField(required=False)
    sld = forms.FileField()


class DatasetTimeSerieForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        _choises = [(None, '-----')] + [(_a.pk, _a.attribute) for _a in kwargs.get('instance').attributes if _a.attribute_type in ['xsd:dateTime']]
        self.base_fields.get('attribute').choices = _choises
        self.base_fields.get('end_attribute').choices = _choises
        super().__init__(*args, **kwargs)

    class Meta:
        model = Attribute
        fields = ('attribute',)

    attribute = forms.ChoiceField(
        required=False,
    )
    end_attribute = forms.ChoiceField(
        required=False,
    )
    presentation = forms.ChoiceField(
        required=False,
        choices=[
            ('LIST', 'List of all the distinct time values'),
            ('DISCRETE_INTERVAL', 'Intervals defined by the resolution'),
            ('CONTINUOUS_INTERVAL', 'Continuous Intervals for data that is frequently updated, resolution describes the frequency of updates')
        ]
    )
    precision_value = forms.IntegerField(required=False)
    precision_step = forms.ChoiceField(required=False, choices=[
        ('years',) * 2,
        ('months',) * 2,
        ('days',) * 2,
        ('hours',) * 2,
        ('minutes',) * 2,
        ('seconds',) * 2
    ])
