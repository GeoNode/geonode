"""Admin sites for the ``study_cases`` app."""
from django.contrib import admin

from .models import StudyCases


class StudyCasesAdmin(admin.ModelAdmin):
    list_display = (
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
    

admin.site.register(StudyCases, StudyCasesAdmin)
