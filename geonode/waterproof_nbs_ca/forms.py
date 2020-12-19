"""
Forms for the ``django - Waterproof NBS`` application.

"""
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from .models import WaterproofNbsCa, RiosTransition, RiosTransformation, RiosActivity,Countries,Currency
from django.contrib.gis.geos import Polygon

class WaterproofNbsCaForm(forms.ModelForm):
    """
    Form to submit a new WaterproofNbsCa.

    """
    
    rios_transitions = forms.ModelChoiceField(queryset=RiosTransition.objects.all())
    rios_activities = forms.ModelChoiceField(queryset=RiosActivity.objects.all())
    rios_transformations = forms.ModelMultipleChoiceField(
        widget=forms.SelectMultiple, queryset=RiosTransformation.objects.all())
    country = forms.ModelChoiceField(queryset=Countries.objects.all())
    currency = forms.ModelChoiceField(queryset=Currency.objects.all())
    transformations_available=forms.ModelMultipleChoiceField(
        widget=forms.SelectMultiple, queryset=RiosTransformation.objects.all())
    def __init__(self, *args, **kwargs):
        super(WaterproofNbsCaForm, self).__init__(*args, **kwargs)
        # without the next line label_from_instance does NOT work
        self.fields['rios_transformations'].queryset = RiosTransformation.objects.all()
        self.fields['rios_transformations'].label_from_instance = lambda obj: "%s" % (obj.name)

    class Meta:
        model = WaterproofNbsCa
        fields = (
            'country',
            'currency',
            'name',
            'description',
            'max_benefit_req_time',
            'profit_pct_time_inter_assoc',
            'total_profits_sbn_consec_time',
            'unit_oportunity_cost',
            'unit_implementation_cost',
            'unit_maintenance_cost',
            'periodicity_maitenance',
            'rios_transitions',
            'rios_activities',
            'transformations_available',
            'rios_transformations',
            'added_by'
        )

    def save(self, *args, **kwargs):
        obj = super(WaterproofNbsCaForm, self).save(*args, **kwargs)
        return obj
