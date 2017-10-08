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

import os
import tempfile
import zipfile
import autocomplete_light
import requests
import shapefile

from django.conf import settings
from django import forms
try:
    import json
except ImportError:
    from django.utils import simplejson as json
from geonode.layers.utils import unzip_file
from geonode.layers.models import Layer, Attribute

autocomplete_light.autodiscover() # flake8: noqa

from geonode.base.forms import ResourceBaseForm
from geonode.settings import MEDIA_ROOT


class JSONField(forms.CharField):

    def clean(self, text):
        text = super(JSONField, self).clean(text)
        try:
            return json.loads(text)
        except ValueError:
            raise forms.ValidationError("this field must be valid JSON")


class LayerForm(ResourceBaseForm):

    class Meta(ResourceBaseForm.Meta):
        model = Layer
        exclude = ResourceBaseForm.Meta.exclude + (
            'workspace',
            'store',
            'storeType',
            'typename',
            'default_style',
            'styles',
            'upload_session',
            'service',
            'status',
            # 'group',
            'last_auditor'
        )


class LayerUploadForm(forms.Form):
    base_file = forms.FileField()
    dbf_file = forms.FileField(required=False)
    shx_file = forms.FileField(required=False)
    prj_file = forms.FileField(required=False)
    xml_file = forms.FileField(required=False)

    charset = forms.CharField(required=False)
    metadata_uploaded_preserve = forms.BooleanField(required=False)

    spatial_files = (
        "base_file",
        "dbf_file",
        "shx_file",
        "prj_file")

    def clean(self):
        cleaned = super(LayerUploadForm, self).clean()
        dbf_file = shx_file = prj_file = xml_file = None
        base_name = base_ext = None
        if zipfile.is_zipfile(cleaned["base_file"]):
            filenames = zipfile.ZipFile(cleaned["base_file"]).namelist()
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

        if base_ext.lower() not in (".shp", ".osm", ".tif", ".tiff", ".geotif", ".geotiff", ".csv"):
            raise forms.ValidationError(
                "Only Shapefiles and GeoTiffs are supported. You uploaded a %s file" %
                base_ext)
        if base_ext.lower() == ".csv" and self.cleaned_data['the_geom'] != "geom" and self.cleaned_data['the_geom'] != '':
            raise forms.ValidationError("The field name of your .csv file which contains multilinestring coordinates should be 'geom' ")
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
                            cleaned["xml_file"].name = '%s.xml' % base_name

        return cleaned

    def write_files(self):

        absolute_base_file = None
        tempdir = tempfile.mkdtemp()
        file = self.cleaned_data['base_file']

	#@jahangir091
        filename = file.name
        extension = os.path.splitext(filename)[1]
        if extension.lower() == '.osm':
            osm_layer_type = self.cleaned_data['osm_layer_type']
            tempdir_osm = tempfile.mkdtemp()  # temporary directory for uploading .osm file
            temporary_file = open('%s/%s' % (tempdir_osm, filename), 'a+')

            for chnk in file.chunks():
                temporary_file.write(chnk)
            temporary_file.close()
            file_path = temporary_file.name
            from geonode.layers.utils import ogrinfo
            response = ogrinfo(file_path)
            if osm_layer_type in response:

                from plumbum.cmd import ogr2ogr
                ogr2ogr[tempdir, file_path, osm_layer_type]()
                files = os.listdir(tempdir)
                for item in files:
                    if item.endswith('.shp'):
                        absolute_base_file = os.path.join(tempdir, item)
            else:
                raise forms.ValidationError('You are trying to upload {0} layer but the .osm file you provided contains'
                                            '{1}'.format(osm_layer_type, response))

        elif extension.lower() == '.csv':
            the_geom = self.cleaned_data['the_geom']
            longitude = self.cleaned_data['longitude'] #longitude
            lattitude = self.cleaned_data['lattitude'] #latitude
            tempdir_csv = tempfile.mkdtemp()  # temporary directory for uploading .csv file
            temporary_file = open('%s/%s' % (tempdir_csv, filename), 'a+')
            for chnk in file.chunks():
                temporary_file.write(chnk)
            temporary_file.close()
            file_path = temporary_file.name

            temp_vrt_path = os.path.join(tempdir_csv, "tempvrt.vrt")
            temp_vrt_file = open(temp_vrt_path, 'wt')
            vrt_string = """  <OGRVRTDataSource>
                    <OGRVRTLayer name="222ogr_vrt_layer_name222">
                    <SrcDataSource>000path_to_the_imported_csv_file000</SrcDataSource>
                    <GeometryType>wkbUnknown</GeometryType>
                    <GeometryField encoding="WKT" field="111the_field_name_geom_for_csv111"/>
                    </OGRVRTLayer>
                    </OGRVRTDataSource> """

            vrt_string_point = """
                <OGRVRTDataSource>
                    <OGRVRTLayer name="222ogr_vrt_layer_name222">
                        <SrcDataSource>000path_to_the_imported_csv_file000</SrcDataSource>
			            <SrcLayer>222ogr_vrt_layer_name222</SrcLayer>
                        <GeometryType>wkbPoint</GeometryType>
		                <LayerSRS>WGS84</LayerSRS>
                        <GeometryField encoding="PointFromColumns" x="333y_for_longitude_values333" y="111x_for_lattitude_values111"/>
                    </OGRVRTLayer>
                </OGRVRTDataSource>"""

            layer_name, ext = os.path.splitext(filename)

            if longitude and lattitude:
                vrt_string_point = vrt_string_point.replace("222ogr_vrt_layer_name222", layer_name)
                vrt_string_point = vrt_string_point.replace("000path_to_the_imported_csv_file000", file_path)
                vrt_string_point = vrt_string_point.replace("111x_for_lattitude_values111", lattitude)
                vrt_string_point = vrt_string_point.replace("333y_for_longitude_values333", longitude)
                temp_vrt_file.write(vrt_string_point)
            elif the_geom:
                vrt_string = vrt_string.replace("222ogr_vrt_layer_name222", layer_name)
                vrt_string = vrt_string.replace("000path_to_the_imported_csv_file000", file_path)
                vrt_string = vrt_string.replace("111the_field_name_geom_for_csv111", the_geom)
                temp_vrt_file.write(vrt_string)

            temp_vrt_file.close()
            ogr2ogr_string = 'ogr2ogr -overwrite -f "ESRI Shapefile" '
            ogr2ogr_string = ogr2ogr_string+'"'+tempdir+'"'+' '+'"'+temp_vrt_path+'"'

            os.system(ogr2ogr_string)

            files = os.listdir(tempdir)
            for item in files:
                if item.endswith('.shp'):
                    shape_file = shapefile.Reader(os.path.join(tempdir, item))
                    shapes = shape_file.shapes()
                    names = [name for name in dir(shapes[1]) if not name.startswith('__')]
                    if not 'bbox' in names and the_geom:
                        raise forms.ValidationError('The "geom" field of your .csv file does not contains valid multistring points '
                                                    'or your uploaded file does not contains valid layer')
                    else:
                        absolute_base_file = os.path.join(tempdir, item)


        elif zipfile.is_zipfile(self.cleaned_data['base_file']):
	#end

            absolute_base_file = unzip_file(self.cleaned_data['base_file'], '.shp', tempdir=tempdir)

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
    if 'geonode.geoserver' in settings.INSTALLED_APPS:
        sld_file = forms.FileField(required=False)
    if 'geonode_qgis_server' in settings.INSTALLED_APPS:
        qml_file = forms.FileField(required=False)
    xml_file = forms.FileField(required=False)

    abstract = forms.CharField(required=False)
    layer_title = forms.CharField(required=True)
    permissions = JSONField()
    charset = forms.CharField(required=False)

    #@jahangir091
    category = forms.CharField(required=True)
    organization = forms.CharField(required=True)
    admin_upload = forms.BooleanField(required=False)
    the_geom = forms.CharField(required=False)
    longitude = forms.CharField(required=False)
    lattitude = forms.CharField(required=False)
    osm_layer_type = forms.CharField(required=False)
    #end

    metadata_uploaded_preserve = forms.BooleanField(required=False)

    spatial_files = [
        "base_file",
        "dbf_file",
        "shx_file",
        "prj_file",
        "xml_file",
    ]
    # Adding style file based on the backend
    if 'geonode.geoserver' in settings.INSTALLED_APPS:
        spatial_files.append('sld_file')
    if 'geonode_qgis_server' in settings.INSTALLED_APPS:
        spatial_files.append('qml_file')

    spatial_files = tuple(spatial_files)


class LayerDescriptionForm(forms.Form):
    title = forms.CharField(300)
    abstract = forms.CharField(1000, widget=forms.Textarea, required=False)
    keywords = forms.CharField(500, required=False)


class LayerAttributeForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(LayerAttributeForm, self).__init__(*args, **kwargs)
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
