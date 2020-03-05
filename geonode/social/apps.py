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

from django.conf import settings
from django.apps import AppConfig


class SocialConfig(AppConfig):
    name = 'geonode.social'

    def ready(self):
        from django.apps import apps
        from actstream import registry
        registry.register(apps.get_app_config('layers').get_model('Layer'))
        registry.register(apps.get_app_config('maps').get_model('Map'))
        registry.register(apps.get_app_config('documents').get_model('Document'))
        registry.register(apps.get_app_config('services').get_model('Service'))
        registry.register(apps.get_app_config('dialogos').get_model('Comment'))
        _auth_user_model = settings.AUTH_USER_MODEL.split('.')
        registry.register(apps.get_app_config(_auth_user_model[0]).get_model(_auth_user_model[1]))
