# -*- coding: utf-8 -*-
import taggit
from django import forms
from geonode.maps.models import Map


class MapForm(forms.ModelForm):
    keywords = taggit.forms.TagField()
    class Meta:
        model = Map
        exclude = ('contact', 'zoom', 'projection', 'center_x', 'center_y', 'owner')
        widgets = {
            'abstract': forms.Textarea(attrs={'cols': 40, 'rows': 10}),
        }


