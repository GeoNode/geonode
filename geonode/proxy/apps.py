#########################################################################
#
# Copyright (C) 2023 OSGeo
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
from django.db.models.signals import post_migrate

from .utils import proxy_urls_registry


def run_setup_hooks(*args, **kwargs):
    proxy_urls_registry.initialize()


class GeoNodeProxyAppConfig(AppConfig):
    name = "geonode.proxy"
    verbose_name = "GeoNode Proxy"

    def ready(self):
        super().ready()
        try:
            run_setup_hooks()
        except Exception:
            # This is in case the Service table doesn't exist yet
            post_migrate.connect(run_setup_hooks, sender=self)
