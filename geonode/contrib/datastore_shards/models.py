# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
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

from geonode.layers.models import Layer

from django.db import models
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _


class Database(models.Model):
    """
    A model representing a database shard.
    """
    YEARLY = 0
    MONTHLY = 1
    LAYERCOUNT = 2
    SHARD_STRATEGY_TYPE = (
        (YEARLY, 'yearly'),
        (MONTHLY, 'monthly'),
        (LAYERCOUNT, 'layercount'),
    )

    name = models.TextField(_("Database Shard Name"))
    layers_count = models.IntegerField(_("Layers Count"), default=0)
    created_at = models.DateTimeField(auto_now=True)
    strategy_type = models.IntegerField(choices=SHARD_STRATEGY_TYPE)

    class Meta:
        verbose_name_plural = 'Shard Databases'


def update_shard_layers_count(instance, sender, **kwargs):
    """
    Update layers_count for Database model.
    """
    store_name = instance.store
    # if layer is part of a shards we need to increment layers_count
    if Database.objects.filter(name=store_name).exists():
        shardatabase = Database.objects.get(name=store_name)
        shardatabase.layers_count = Layer.objects.filter(store=store_name).count()
        shardatabase.save()


signals.post_delete.connect(update_shard_layers_count, sender=Layer)
signals.post_save.connect(update_shard_layers_count, sender=Layer)
