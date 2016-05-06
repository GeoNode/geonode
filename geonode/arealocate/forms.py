import os
import string
import traceback

from django import forms

from pprint import pprint

class GeocodeForm(forms.Form):
    geocode_input = forms.CharField(label='Area To Locate', max_length=255)
    
    def clean_geocode_input(self):
        valid_ch = string.lowercase + string.uppercase + string.digits+",.-#' "
        
        for x in self.cleaned_data.get("geocode_input"):
            if x not in valid_ch:
                pprint("error on validation")
                raise forms.ValidationError("Invalid Place Name Format")
        
        return self.cleaned_data.get("geocode_input")

