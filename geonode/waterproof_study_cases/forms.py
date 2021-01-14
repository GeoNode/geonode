"""
Forms for the ``django - Study Case`` application.

"""
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from .models import StudyCases


class StudyCasesForm(forms.ModelForm):
    """
    Form to submit a new Study Case.

    """
    class Meta:
        model = StudyCases
        fields = (
            'dws_name', 
            'dws_description',
            'dws_analysis_period_value', 
            'dws_type_money',
            'dws_benefit_function',
            'estado_id',
            'dws_rio_analysis_time',
            'dws_time_implement_briefcase',
            'dws_annual_investment_scenario',
            'dws_time_implement_scenario',
            'dws_climate_scenario_scenario',
            'region_id',
            'ciudad_id',
            'dws_authorization_case',
            'dws_id_parent',
            'dws_benefit_carbon_market'
        )    

    def save(self, *args, **kwargs):
        
        obj = super(StudyCasesForm, self).save(*args, **kwargs)
        return obj
