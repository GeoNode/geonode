#########################################################################
#
# Copyright (C) 2026 OSGeo
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
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from geonode.security.models import AuthConfig


class DataItem(models.Model):
    """
    Uniform handle on something a source provider can read (e.g. a PostGIS table), read through its connection.
    Not a ResourceBase: the catalog will point at it, it is not part of the catalog.
    """

    # every discovery upsert draws a sequence value, also for the rows already known
    id = models.BigAutoField(primary_key=True)
    # soft reference to the registry by key, set once at creation: an uninstalled provider leaves the item unreadable
    source_provider = models.CharField(max_length=64, db_index=True)
    uri = models.TextField(help_text=_("Provider-owned location of the item inside its connection, without secrets"))
    # deleting a connection drops its items: only GeoNode rows, never the upstream data
    auth_config = models.ForeignKey(AuthConfig, on_delete=models.CASCADE, related_name="data_items")
    title = models.TextField(blank=True, default="")
    # cached at discovery, so that listing the items never reaches the provider
    details = models.JSONField(blank=True, default=dict)
    # gone upstream at the last discovery: kept, the catalog may still point at it
    is_available = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["auth_config", "uri"], name="sources_dataitem_unique_auth_config_uri"),
        ]

    def __str__(self):
        return f"{self.source_provider}:{self.uri}"
