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


"""Models for the ``WaterProof NBS CA`` app."""

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class WaterproofNbsCa(models.Model):
    """
    Model to Waterproof.

    :name: Waterproof Name.


    """
    RIOS_TRANSITION = (
        ('nv', _('Keep native vegetation')),
        ('rvU', _('Revegetation (unassisted)')),
        ('rvA', _('Revegetation (assisted)')),
        ('nv', _('Agricultural vegetation management')),
        ('di', _('Ditching')),
        ('rvA', _('Pasture management')),
        ('rvA', _('Fertilizer management')),
    )

    LAND_COVERS = (
        ('Forest', _('Forest')),
        ('Grassland', _('Grassland')),
        ('Shrubland', _('Shrubland')),
        ('Sparse vegetation', _('Sparse vegetation')),
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
    )

    description = models.CharField(
        max_length=1024,
        verbose_name=_('Description'),
    )

    max_benefit_req_time = models.IntegerField(
        default=0,
        verbose_name=_('Time maximum benefit'),
    )

    profit_pct_time_inter_assoc = models.FloatField(
        default=0,
        verbose_name=_('Percentage of benefit associated with interventions at time t=0'),
    )

    total_profits_sbn_consec_time = models.IntegerField(
        default=0,
        verbose_name=_('Procurement time of total SBN benefits'),
    )

    unit_implementation_cost = models.FloatField(
        default=0,
        verbose_name=_('Unit implementation costs (US $/ha)'),
    )

    unit_maintenance_cost = models.FloatField(
        default=0,
        verbose_name=_('Unit maintenance costs (US $/ha)'),
    )

    periodicity_maitenance = models.IntegerField(
        default=0,
        verbose_name=_('Periodicity of maintenance (year)'),
    )

    unit_oportunity_cost = models.IntegerField(
        default=0,
        verbose_name=_('Unit oportunity costs (US $/ha)'),
    )

    rios_transition = models.CharField(
        max_length=32,
        choices=RIOS_TRANSITION,
        default='1'
    )

    land_cover_def = models.CharField(
        max_length=32,
        choices=LAND_COVERS,
        default=''
    )

    class Meta:
        ordering = ['name', 'description']

    def get_entries(self):
        return self.entries.filter(published=True).annotate(
            null_position=models.Count('fixed_position')).order_by(
            '-null_position', 'fixed_position', '-amount_of_views')
