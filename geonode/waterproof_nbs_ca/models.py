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
from django.contrib.gis.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class ActivityShapefile(models.Model):
    activity = models.CharField(max_length=255)
    action = models.CharField(max_length=255)
    area = models.MultiPolygonField()


class RiosTransition(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
    )
    description = models.CharField(
        max_length=1024,
        verbose_name=_('Description'),
    )

    def __str__(self):
        return "%s" % self.name


class RiosActivity(models.Model):
    transition = models.ForeignKey(RiosTransition, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
    )
    description = models.CharField(
        max_length=1024,
        verbose_name=_('Description'),
    )

    def __str__(self):
        return "%s" % self.name


class RiosTransformation(models.Model):
    activity = models.ForeignKey(RiosActivity, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
    )
    description = models.CharField(
        max_length=1024,
        verbose_name=_('Description'),
    )
    unique_id = models.CharField(
        max_length=1024,
        verbose_name=_('Unique_id'),
    )

    def __str__(self):
        return "%s" % self.name


class Region(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
    )

    def __str__(self):
        return "%s" % self.name


class Countries(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
    )

    code = models.CharField(
        max_length=5,
        verbose_name=_('Code'),
    )

    factor = models.FloatField(
        default=0,
        verbose_name=_('Factor'),
    )

    def __str__(self):
        return "%s" % self.name


class Currency(models.Model):
    country = models.ForeignKey(Countries, on_delete=models.CASCADE)

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
    )

    code = models.CharField(
        max_length=50,
        verbose_name=_('Code'),
    )

    factor = models.CharField(
        max_length=50,
        verbose_name=_('Factor'),
    )

    def __str__(self):
        return "(%s)" % self.code


class WaterproofNbsCa(models.Model):
    """
    Model to Waterproof.

    :name: Waterproof Name.

    """
    country = models.ForeignKey(Countries, on_delete=models.CASCADE)

    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
    )

    description = models.CharField(
        max_length=2048,
        verbose_name=_('Description'),
    )

    max_benefit_req_time = models.IntegerField(
        default=0,
        verbose_name=_('Time maximum benefit'),
    )

    profit_pct_time_inter_assoc = models.IntegerField(
        default=0,
        verbose_name=_('Percentage of benefit associated with interventions at time t=0'),
    )

    total_profits_sbn_consec_time = models.IntegerField(
        default=0,
        verbose_name=_('Procurement time of total SBN benefits'),
    )

    unit_implementation_cost = models.DecimalField(
        decimal_places=4,
        max_digits=14,
        verbose_name=_('Unit implementation costs (US $/ha)'),
    )

    unit_maintenance_cost = models.DecimalField(
        decimal_places=4,
        max_digits=14,
        verbose_name=_('Unit maintenance costs (US $/ha)'),
    )

    periodicity_maitenance = models.IntegerField(
        default=0,
        verbose_name=_('Periodicity of maintenance (year)'),
    )

    unit_oportunity_cost = models.DecimalField(
        decimal_places=4,
        max_digits=14,
        verbose_name=_('Unit oportunity costs (US $/ha)'),
    )

    rios_transformations = models.ManyToManyField(
        RiosTransformation,
    )

    activity_shapefile = models.ForeignKey(
        ActivityShapefile,
        on_delete=models.CASCADE
    )

    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ['name', 'description']

    def get_entries(self):
        return self.entries.filter(published=True).annotate(
            null_position=models.Count('fixed_position')).order_by(
            '-null_position', 'fixed_position', '-amount_of_views')
