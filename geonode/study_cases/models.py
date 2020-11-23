# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2020 WFApp
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################


"""Models for the ``study_cases`` app."""

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

class StudyCases(models.Model):
    """
    Model to gather answers in topic groups.

    :name: Study Case Name.
    

    """
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
    )

    description = models.CharField(
        max_length=1024,
        verbose_name=_('Description'),
    )

    treatment_plants = models.CharField(
        max_length=255,
        verbose_name=_('Treatment Plants'),
    )

    water_intakes = models.CharField(
        max_length=255,
        verbose_name=_('Water Intakes'),
    )

    with_carbon_markets = models.BooleanField(
        _('Carbon Markets'),
        default=False,
    )

    erosion_control_drinking_water_qa = models.BooleanField(
        _('Erosion Control For Drinking Water Quality'),
        default=False,
    )

    nutrient_retention_ph = models.BooleanField(
        _('Nutrient Retention - Phosphorus'),
        default=False,
    )

    nutrient_retention_ni = models.BooleanField(
        _('Nutrient Retention - Nitrogen'),
        default=False,
    )

    flood_mitigation = models.BooleanField(
        _('Flood Mitigation'),
        default=False,
    )

    groundwater_recharge_enhancement = models.BooleanField(
        _('Groundwater Recharge Enhancement'),
        default=False,
    )

    baseflow = models.BooleanField(
        _('Baseflow'),
        default=False,
    )

    annual_water_yield = models.CharField(
        max_length=1024,
        verbose_name=_('Annual Water Yield'),
    )

    sediment_delivery_ratio = models.CharField(
        max_length=1024,
        verbose_name=_('Sediment Delivery Radio'),
    )

    nutrient_delivery = models.CharField(
        max_length=1024,
        verbose_name=_('Nutrient Delivery'),
    )

    seasonal_water_yield = models.CharField(
        max_length=1024,
        verbose_name=_('Seasonal Water Yield'),
    )

    carbon_storage = models.CharField(
        max_length=1024,
        verbose_name=_('Carbon Storage'),
    )

    platform_cost_per_year  = models.FloatField(
        default=0,
        verbose_name=_('Platform Cost Per Year'),
    )

    personnel_salary_benefits  = models.FloatField(
        default=0,
        verbose_name=_('Personal Salary and Benefits'),
    )

    program_director  = models.FloatField(
        default=0,
        verbose_name=_('Program Director'),
    )

    monitoring_and_evaluation_mngr  = models.FloatField(
        default=0,
        verbose_name=_('Monitoring And Evaluation Manager'),
    )

    finance_and_admin  = models.FloatField(
        default=0,
        verbose_name=_('Finance and Administrator'),
    )

    implementation_manager  = models.FloatField(
        default=0,
        verbose_name=_('Implementation Manager'),
    )

    office_costs  = models.FloatField(
        default=0,
        verbose_name=_('Office Costs'),
    )

    travel  = models.FloatField(
        default=0,
        verbose_name=_('Travel'),
    )

    equipment  = models.FloatField(
        default=0,
        verbose_name=_('Equipment'),
    )

    contracts  = models.FloatField(
        default=0,
        verbose_name=_('Contracts'),
    )

    overhead  = models.FloatField(
        default=0,
        verbose_name=_('Overhead'),
    )

    others  = models.FloatField(
        default=0,
        verbose_name=_('Others'),
    )

    transaction_costs  = models.FloatField(
        default=0,
        verbose_name=_('Transaction Cost'),
    )

    discount_rate  = models.FloatField(
        default=0,
        verbose_name=_('Discount Rate'),
    )

    sensitive_analysis_min_disc_rate  = models.FloatField(
        default=0,
        verbose_name=_('Sentivity Analysys - Min Discount Rate'),
    )

    sensitive_analysis_max_disc_rate  = models.FloatField(
        default=0,
        verbose_name=_('Sentivity Analysys - Max Discount Rate'),
    )

    nbs_ca_conservation = models.BooleanField(
        _('Conservation'),
        default=False,
    )

    nbs_ca_active_restoration = models.BooleanField(
        _('Active Restoration'),
        default=False,
    )

    nbs_ca_passive_restoration = models.BooleanField(
        _('Passive Restoration'),
        default=False,
    )

    nbs_ca_agroforestry = models.BooleanField(
        _('Agroforestry'),
        default=False,        
    )

    nbs_ca_silvopastoral = models.BooleanField(
        _('Silvopastoral'),
        default=False,
    )
    

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', 'description']

    def get_entries(self):
        return self.entries.filter(published=True).annotate(
            null_position=models.Count('fixed_position')).order_by(
            '-null_position', 'fixed_position', '-amount_of_views')



