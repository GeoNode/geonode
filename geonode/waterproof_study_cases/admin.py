"""Admin sites for the ``study_cases`` app."""
from django.contrib import admin

from .models import StudyCases


class StudyCasesAdmin(admin.ModelAdmin):
    list_display = (
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


admin.site.register(StudyCases, StudyCasesAdmin)
