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
    from django.conf import settings
    from .celery_app import app as celery_app

    if celery_app not in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS += (celery_app,)


class AppConfig(BaseAppConfig):
    name = "geonode"
    label = "geonode"

    def ready(self):
        super().ready()
        run_setup_hooks()
