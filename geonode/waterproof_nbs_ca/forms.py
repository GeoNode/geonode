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
            'max_benefit_req_time',
            'profit_pct_time_inter_assoc',
            'total_profits_sbn_consec_time',
            'unit_implementation_cost',
            'unit_maintenance_cost',
            'periodicity_maitenance',
            'unit_oportunity_cost',
            'rios_transition',
            'land_cover_def'
        )

    def save(self, *args, **kwargs):

        obj = super(WaterproofNbsCaForm, self).save(*args, **kwargs)
        return obj
