"""
Forms for the ``django - Waterproof Intake`` application.

"""

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from .models import Intake

class IntakeForm(forms.ModelForm):    

    class Meta:
        model = Intake
        fields = ('name', 
                'description',
                'water_source_name'
        )
        """
                'id_region', 
                'id_city')
        widgets = {'id_region': forms.HiddenInput(),
                    'id_city': forms.HiddenInput()}
        """
    def save(self, *args, **kwargs):
        
        obj = super(IntakeForm, self).save(*args, **kwargs)
        return obj