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

import os
import tempfile
import taggit

from django import forms
from django.utils import simplejson as json
from django.utils.translation import ugettext_lazy as _

from geonode.layers.models import Layer, Attribute
from geonode.people.models import Profile 


class JSONField(forms.CharField):
    def clean(self, text):
        text = super(JSONField, self).clean(text)
        try:
            return json.loads(text)
        except ValueError:
            raise forms.ValidationError("this field must be valid JSON")


class LayerForm(forms.ModelForm):
    date = forms.DateTimeField(widget=forms.SplitDateTimeWidget)
    date.widget.widgets[0].attrs = {"class":"date"}
    date.widget.widgets[1].attrs = {"class":"time"}
    temporal_extent_start = forms.DateField(required=False,widget=forms.DateInput(attrs={"class":"date"}))
    temporal_extent_end = forms.DateField(required=False,widget=forms.DateInput(attrs={"class":"date"}))

    poc = forms.ModelChoiceField(empty_label = "Person outside GeoNode (fill form)",
                                 label = "Point Of Contact", required=False,
                                 queryset = Profile.objects.exclude(user=None))

    metadata_author = forms.ModelChoiceField(empty_label = "Person outside GeoNode (fill form)",
                                             label = "Metadata Author", required=False,
                                             queryset = Profile.objects.exclude(user=None))
    keywords = taggit.forms.TagField(required=False,
                                     help_text=_("A space or comma-separated list of keywords"))
    class Meta:
        model = Layer
        exclude = ('contacts','workspace', 'store', 'name', 'uuid', 'storeType', 'typename',
                   'bbox_x0', 'bbox_x1', 'bbox_y0', 'bbox_y1', 'srid',
                   'csw_typename', 'csw_schema', 'csw_mdsource', 'csw_type',
                   'csw_wkt_geometry', 'metadata_uploaded', 'metadata_xml', 'csw_anytext',
                   'popular_count', 'share_count', 'thumbnail', 'default_style', 'styles')

class LayerUploadForm(forms.Form):
    base_file = forms.FileField()
    dbf_file = forms.FileField(required=False)
    shx_file = forms.FileField(required=False)
    prj_file = forms.FileField(required=False)
    xml_file = forms.FileField(required=False)

    spatial_files = ("base_file", "dbf_file", "shx_file", "prj_file")

    def clean(self):
        cleaned = super(LayerUploadForm, self).clean()
        base_name, base_ext = os.path.splitext(cleaned["base_file"].name)
        if base_ext.lower() == '.zip':
            # for now, no verification, but this could be unified
            pass
        elif base_ext.lower() not in (".shp", ".tif", ".tiff", ".geotif", ".geotiff"):
            raise forms.ValidationError("Only Shapefiles and GeoTiffs are supported. You uploaded a %s file" % base_ext)
        if base_ext.lower() == ".shp":
            dbf_file = cleaned["dbf_file"]
            shx_file = cleaned["shx_file"]
            if dbf_file is None or shx_file is None:
                raise forms.ValidationError("When uploading Shapefiles, .SHX and .DBF files are also required.")
            dbf_name, __ = os.path.splitext(dbf_file.name)
            shx_name, __ = os.path.splitext(shx_file.name)
            if dbf_name != base_name or shx_name != base_name:
                raise forms.ValidationError("It looks like you're uploading "
                    "components from different Shapefiles. Please "
                    "double-check your file selections.")
            if cleaned["prj_file"] is not None:
                prj_file = cleaned["prj_file"].name
                if os.path.splitext(prj_file)[0] != base_name:
                    raise forms.ValidationError("It looks like you're "
                        "uploading components from different Shapefiles. "
                        "Please double-check your file selections.")
            if cleaned["xml_file"] is not None:
                xml_file = cleaned["xml_file"].name
                if os.path.splitext(xml_file)[0] != base_name:
                    if xml_file.find('.shp') != -1:
                        # force rename of file so that file.shp.xml doesn't overwrite as file.shp
                        cleaned["xml_file"].name = '%s.xml' % base_name
        return cleaned

    def write_files(self):
        tempdir = tempfile.mkdtemp()
        for field in self.spatial_files:
            f = self.cleaned_data[field]
            if f is not None:
                path = os.path.join(tempdir, f.name)
                with open(path, 'w') as writable:
                    for c in f.chunks():
                        writable.write(c)
        absolute_base_file = os.path.join(tempdir,
                self.cleaned_data["base_file"].name)
        return tempdir, absolute_base_file


class NewLayerUploadForm(LayerUploadForm):
    sld_file = forms.FileField(required=False)
    xml_file = forms.FileField(required=False)

    abstract = forms.CharField(required=False)
    layer_title = forms.CharField(required=False)
    permissions = JSONField()

    spatial_files = ("base_file", "dbf_file", "shx_file", "prj_file", "sld_file", "xml_file")


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
        exclude = ('attribute_type',)

class LayerStyleUploadForm(forms.Form):
    layerid = forms.IntegerField()
    name = forms.CharField(required=False)
    update = forms.BooleanField(required=False)
    sld = forms.FileField()
