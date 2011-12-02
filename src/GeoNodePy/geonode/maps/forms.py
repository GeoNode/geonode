# -*- coding: UTF-8 -*-
from django import forms
import json
import os
import tempfile
from django.utils.translation import ugettext as _

SRS_CHOICES = (
    ('EPSG:4326', 'EPSG:4326 (WGS 84 Lat/Long)'),
    ('EPSG:900913', 'EPSG:900913 (Web Mercator)'),
)

GEOMETRY_CHOICES = [
    ['Point', 'Points'],
    ['LineString', 'Lines'],
    ['Polygon', 'Polygons (Shapes)']
]


TYPE_CHOICES = (
       ('java.lang.Boolean', 'Boolean (true/false)'),
       ('java.util.Date', 'Date/Time'),
       ('java.lang.Float', 'Number (Float)'),
       ('java.lang.Integer', 'Number (Integer)'),
       ('java.lang.String', 'Text'),
)


LAYER_SCHEMA_TEMPLATE = "Name:java.lang.String,Description:java.lang.String,Start_Date:java.util.Date,End_Date:java.util.Date,String_Value_1:java.lang.String,String_Value_2:java.lang.String,Number_Value_1:java.lang.Float,Number_Value_2:java.lang.Float"

class JSONField(forms.CharField):
    def clean(self, text):
        text = super(JSONField, self).clean(text)
        try:
            return json.loads(text)
        except ValueError:
            raise forms.ValidationError("this field must be valid JSON")


class LayerCreateForm(forms.Form):
    name = forms.CharField(label="Name", max_length=256,required=True)
    title = forms.CharField(label="Title",max_length=256,required=True)
    srs = forms.CharField(label="Projection",initial="EPSG:4326",required=True)
    geom = forms.ChoiceField(label="Data type", choices=GEOMETRY_CHOICES,required=True)
    keywords = forms.CharField(label = '*' + _('Keywords (separate with spaces)'), widget=forms.Textarea)
    abstract = forms.CharField(widget=forms.Textarea, label="Abstract", required=True)
    permissions = JSONField()

class LayerUploadForm(forms.Form):
    base_file = forms.FileField()
    dbf_file = forms.FileField(required=False)
    shx_file = forms.FileField(required=False)
    prj_file = forms.FileField(required=False)
    sld_file = forms.FileField(required=False)
    encoding = forms.ChoiceField(required=False)
    spatial_files = ("base_file", "dbf_file", "shx_file", "prj_file", "sld_file")

    def clean(self):
        cleaned = super(LayerUploadForm, self).clean()

        base_name, base_ext = os.path.splitext(cleaned["base_file"].name)
        if base_ext.lower() not in (".shp", ".tif", ".tiff", ".geotif", ".geotiff", ".zip"):
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
        absolute_base_file = os.path.join(tempdir, self.cleaned_data["base_file"].name)
        sld_file = None
        if self.cleaned_data["sld_file"]:
            sld_file = os.path.join(tempdir, self.cleaned_data["sld_file"].name)
        return tempdir,  absolute_base_file, sld_file

class WorldMapLayerUploadForm(LayerUploadForm):
    sld_file = forms.FileField(required=False)
    encoding = forms.ChoiceField(required=False)
    abstract = forms.CharField(required=False)
    keywords = forms.CharField(required=False)
    layer_title = forms.CharField(required=False)
    keywords = forms.CharField(required=False)
    permissions = JSONField()

    spatial_files = ("base_file", "dbf_file", "shx_file", "prj_file", "sld_file")
