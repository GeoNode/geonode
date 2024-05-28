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
from django.apps import AppConfig

from geonode.notifications_helper import NotificationsAppConfigBase


class BaseAppConfig(NotificationsAppConfigBase, AppConfig):
    name = "geonode.assets"

    def ready(self):
        super().ready()
        run_setup_hooks()


def run_setup_hooks(*args, **kwargs):
    from geonode.assets.handlers import asset_handler_registry

    asset_handler_registry.init_registry()
