# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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

from tastypie.authorization import DjangoAuthorization
from tastypie.exceptions import Unauthorized

from guardian.shortcuts import get_objects_for_user

from geonode.layers.models import Layer


class GeoNodeDJMPAuthorization(DjangoAuthorization):

    """Object level API authorization based on GeoNode granular
    permission system"""

    def read_list(self, object_list, bundle):
        permitted_uuids = get_objects_for_user(
            bundle.request.user,
            'base.view_resourcebase').values('uuid')
        return object_list.filter(layer_uuid__in=permitted_uuids)

    def read_detail(self, object_list, bundle):
        return bundle.request.user.has_perm(
            'view_resourcebase',
            Layer.objects.get(uuid=bundle.obj.layer_uuid))

    def create_list(self, object_list, bundle):
        # TODO implement if needed
        raise Unauthorized()

    def create_detail(self, object_list, bundle):
        return bundle.request.user.has_perm(
            'add_resourcebase',
            Layer.objects.get(uuid=bundle.obj.layer_uuid))

    def update_list(self, object_list, bundle):
        # TODO implement if needed
        raise Unauthorized()

    def update_detail(self, object_list, bundle):
        return bundle.request.user.has_perm(
            'change_resourcebase',
            Layer.objects.get(uuid=bundle.obj.layer_uuid))

    def delete_list(self, object_list, bundle):
        # TODO implement if needed
        raise Unauthorized()

    def delete_detail(self, object_list, bundle):
        return bundle.request.user.has_perm(
            'delete_resourcebase',
            Layer.objects.get(uuid=bundle.obj.layer_uuid))
