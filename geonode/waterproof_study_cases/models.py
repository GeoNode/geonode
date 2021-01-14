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
    dws_name = models.CharField(max_length=100, blank=True, null=True)
    dws_description = models.CharField(max_length=500, blank=True, null=True)
    dws_analysis_period_value = models.IntegerField(blank=True, null=True)
    dws_type_money = models.CharField(max_length=10, blank=True, null=True)
    dws_benefit_function = models.CharField(max_length=100, blank=True, null=True)
    estado_id = models.IntegerField(blank=True, null=True)
    dws_usr_create = models.IntegerField(blank=True, null=True)
    dws_create_date = models.DateTimeField(blank=True, null=True)
    dws_modif_date = models.DateTimeField(blank=True, null=True)
    dws_rio_analysis_time = models.IntegerField()
    dws_time_implement_briefcase = models.IntegerField(blank=True, null=True)
    dws_climate_scenario_briefcase = models.CharField(max_length=100, blank=True, null=True)
    dws_annual_investment_scenario = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    dws_time_implement_scenario = models.IntegerField(blank=True, null=True)
    dws_climate_scenario_scenario = models.CharField(max_length=100, blank=True, null=True)
    region_id = models.IntegerField(blank=True, null=True)
    ciudad_id = models.IntegerField(blank=True, null=True)
    dws_authorization_case = models.CharField(max_length=20)
    dws_id_parent = models.IntegerField(blank=True, null=True)
    dws_benefit_carbon_market = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'waterproof_study_cases'
 
