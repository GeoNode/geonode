from django import forms
from geonode.layers.models import Layer

class LayerUploadForm(forms.Form): 
    title = forms.CharField(max_length=100)
    data_file = forms.FileField(max_length=200)
    
    class Meta:
        mode = Layer
