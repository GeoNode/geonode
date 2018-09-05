# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 OSGeo
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
from django.apps import AppConfig as BaseAppConfig


def run_setup_hooks(*args, **kwargs):
    from .signals import register_qgis_server_signals
    register_qgis_server_signals()


class AppConfig(BaseAppConfig):

    name = "geonode.qgis_server"
    label = "qgis_server"

    def ready(self):
        super(AppConfig, self).ready()
        run_setup_hooks()
