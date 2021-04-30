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

from django.conf import settings
from django.core.management.base import BaseCommand
from geonode.layers.models import Layer
from geonode.security.utils import set_geofence_all
import logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Resets Permissions to Public for All Layers
    """

    def handle(self, *args, **options):
        all_layers = Layer.objects.all()

        for index, layer in enumerate(all_layers):
            print(f"[{index + 1} / {len(all_layers)}] Setting public permissions to Layer [{layer.name}] ...")
            try:
                use_geofence = settings.OGC_SERVER['default'].get(
                    "GEOFENCE_SECURITY_ENABLED", False)
                if use_geofence:
                    set_geofence_all(layer)
                layer.set_default_permissions()
                perm_spec = {"users": {}, "groups": {}}
                perm_spec["users"]["admin"] = ['view_resourcebase', 'change_resourcebase_permissions',
                                               'download_resourcebase', 'publish_resourcebase',
                                               'change_resourcebase_metadata']
                perm_spec["users"][str(layer.owner)] = ['view_resourcebase', 'change_resourcebase_permissions',
                                                        'download_resourcebase', 'publish_resourcebase',
                                                        'change_resourcebase_metadata']
                perm_spec["users"]["AnonymousUser"] = ['view_resourcebase', 'download_resourcebase']
                layer.set_permissions(perm_spec)
            except Exception:
                logger.error(f"[ERROR] Layer [{layer.name}] couldn't be updated")
