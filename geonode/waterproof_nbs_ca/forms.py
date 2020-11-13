"""
Forms for the ``django - Study Case`` application.

"""
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from .models import WaterproofNbsCa


class WaterproofNbsCaForm(forms.ModelForm):
    """
    Form to submit a new WaterproofNbsCa.

    """
    class Meta:
        model = WaterproofNbsCa
        fields = (
            'name', 
            'description',
            
        )    

    def save(self, *args, **kwargs):
        
        obj = super(WaterproofNbsCaForm, self).save(*args, **kwargs)
        return obj
