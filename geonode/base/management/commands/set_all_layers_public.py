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

from django.core.management.base import BaseCommand
from guardian.shortcuts import get_objects_for_user
from geonode.people.models import Profile
from geonode.layers.models import Layer
from geonode.security.models import set_geofence_all


class Command(BaseCommand):
    """Resets Permissions to Public for All Layers
    """

    def handle(self, *args, **options):
        profiles = Profile.objects.filter(is_superuser=False)
        authorized_layers = list(get_objects_for_user(profiles[0], 'base.view_resourcebase').values('id'))
        all_layers = Layer.objects.all()
        unprotected_layers = Layer.objects.filter(id__in=[d['id'] for d in authorized_layers])
        protected_layers = Layer.objects.all().exclude(id__in=[d['id'] for d in authorized_layers])

        for index, layer in enumerate(all_layers):
            print "[%s / %s] Setting public permissions to Layer [%s] ..." % ((index + 1), len(all_layers), layer.name)
            try:
                set_geofence_all(layer)
                layer.set_default_permissions()
                perm_spec = {"users": {}, "groups": {}}
                perm_spec["users"]["admin"] = ['view_resourcebase','change_resourcebase_permissions','download_resourcebase','publish_resourcebase','change_resourcebase_metadata']
                perm_spec["users"][str(layer.owner)] = ['view_resourcebase','change_resourcebase_permissions','download_resourcebase','publish_resourcebase','change_resourcebase_metadata']
                perm_spec["users"]["AnonymousUser"] = ['view_resourcebase','download_resourcebase']
                layer.set_permissions(perm_spec)
            except:
                print "[ERROR] Layer [%s] couldn't be updated" % (layer.name)
