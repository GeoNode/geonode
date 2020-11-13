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
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
    )

    description = models.CharField(
        max_length=1024,
        verbose_name=_('Description'),
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', 'description']

    def get_entries(self):
        return self.entries.filter(published=True).annotate(
            null_position=models.Count('fixed_position')).order_by(
            '-null_position', 'fixed_position', '-amount_of_views')



