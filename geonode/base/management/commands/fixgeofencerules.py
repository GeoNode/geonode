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
from geonode.security.models import set_geofence_all, set_geofence_owner
from geonode.security.models import get_users_with_perms


class Command(BaseCommand):
    """Creates Rules on GeoFence for Public and Protected Layers
    """

    def handle(self, *args, **options):
        profiles = Profile.objects.filter(is_superuser=False)
        authorized = list(get_objects_for_user(profiles[0], 'base.view_resourcebase').values('id'))
        layers = Layer.objects.filter(id__in=[d['id'] for d in authorized])

        for index, layer in enumerate(layers):
            print "[%s / %s] Setting default permissions to Layer [%s] ..." % ((index + 1), len(layers), layer.name)
            try:
                set_geofence_all(layer)
            except:
                print "[ERROR] Layer [%s] couldn't be updated" % (layer.name)

        protected_layers = Layer.objects.all().exclude(id__in=[d['id'] for d in authorized])

        for index, layer in enumerate(protected_layers):
            print "[%s / %s] Setting owner permissions to Layer [%s] ..." \
                  % ((index + 1), len(protected_layers), layer.name)
            try:
                perms = get_users_with_perms(layer)
                for profile in perms.keys():
                    print " - [%s / %s]" % (str(profile), layer.name)
                    geofence_user = str(profile)
                    if "AnonymousUser" in geofence_user:
                        geofence_user = None
                    set_geofence_owner(layer, geofence_user, view_perms=True, download_perms=True)
            except:
                print "[ERROR] Layer [%s] couldn't be updated" % (layer.name)
