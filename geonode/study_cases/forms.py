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
            'name', 
            'description',
            'treatment_plants', 
            'water_intakes',
            'with_carbon_markets',
            'erosion_control_drinking_water_qa',
            'nutrient_retention_ph',
            'nutrient_retention_ni',
            'flood_mitigation',
            'groundwater_recharge_enhancement',
            'baseflow',
            'annual_water_yield',
            'sediment_delivery_ratio',
            'nutrient_delivery',
            'seasonal_water_yield',
            'carbon_storage',
            'platform_cost_per_year',
            'personnel_salary_benefits',
            'program_director',
            'monitoring_and_evaluation_mngr',
            'finance_and_admin',
            'implementation_manager',
            'office_costs',
            'travel',
            'equipment',
            'contracts',
            'overhead',
            'others',
            'transaction_costs',
            'discount_rate',
            'sensitive_analysis_min_disc_rate',
            'sensitive_analysis_max_disc_rate',
            'nbs_ca_conservation',
            'nbs_ca_active_restoration',
            'nbs_ca_passive_restoration',
            'nbs_ca_agroforestry',
            'nbs_ca_silvopastoral',
        )    

    def save(self, *args, **kwargs):
        
        obj = super(StudyCasesForm, self).save(*args, **kwargs)
        return obj
