# -*- coding: UTF-8 -*-
from django import forms
import json, os, tempfile

class JSONField(forms.CharField):
    def clean(self, text):
        text = super(JSONField, self).clean(text)
        try:
            return json.loads(text)
        except ValueError:
            raise forms.ValidationError("this field must be valid JSON")

class LayerUploadForm(forms.Form):
    base_file = forms.FileField()
    dbf_file = forms.FileField(required=False)
    shx_file = forms.FileField(required=False)
    prj_file = forms.FileField(required=False)
    encoding = forms.ChoiceField(required=False)
    spatial_files = ("base_file", "dbf_file", "shx_file", "prj_file")

    def clean(self):
        cleaned = super(LayerUploadForm, self).clean()
        base_ext = cleaned["base_file"].name[-4:].lower()
        if base_ext not in (".shp", ".tif", ".zip", ".tiff", ".geotif", ".geotiff"):
            raise forms.ValidationError("Only Shapefiles and GeoTiffs are supported. You uploaded a %s file" % base_ext)
        if base_ext == ".shp":
            if cleaned["dbf_file"] is None or cleaned["shx_file"] is None:
                raise forms.ValidationError("When uploading Shapefiles, .SHX and .DBF files are also required.")
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

class NewLayerUploadForm(LayerUploadForm):
    sld_file = forms.FileField(required=False)
    encoding = forms.ChoiceField(required=False)
    abstract = forms.CharField(required=False)
    layer_title = forms.CharField(required=False)
    permissions = JSONField()

    spatial_files = ("base_file", "dbf_file", "shx_file", "prj_file", "sld_file")
