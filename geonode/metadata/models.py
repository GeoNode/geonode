#########################################################################
#
# Copyright (C) 2024 OSGeo
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
import json
from django.db import models

from django.dispatch import receiver
from django.db.models import signals
from django.core.cache import caches
from geonode.metadata import metadata_path


class UISchemaModel(models.Model):
    title = models.CharField(max_length=100)
    ui_schema_json = models.JSONField()
    active = models.BooleanField()

    class Meta:
        verbose_name = "Ui Schema"
        verbose_name_plural = "Ui Schema Management"

    def __str__(self) -> str:
        return self.title


@receiver(signals.post_save, sender=UISchemaModel)
def post_save_uischema(instance, sender, created, **kwargs):
    uischema_cache = caches["uischema_cache"]
    schema = uischema_cache.get("uischema")
    if schema:
        uischema_cache.delete("uischema")
    uischema_cache.set("uischema", instance.ui_schema_json, 3600)
