#########################################################################
#
# Copyright (C) 2024 OSGeo
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
import logging
from django.apps import AppConfig
from django.conf import settings
from django.utils.module_loading import import_string
from geonode.upload.settings import SYSTEM_HANDLERS

logger = logging.getLogger("importer")


class HandlersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "geonode.upload.handlers"

    def ready(self):
        """Finalize setup"""
        run_setup_hooks()
        super(HandlersConfig, self).ready()


def run_setup_hooks(*args, **kwargs):
    available_handlers = settings.IMPORTER_HANDLERS + SYSTEM_HANDLERS
    _handlers = [import_string(module_path) for module_path in available_handlers]
    for item in _handlers:
        item.register()
    logger.info(f"The following handlers have been registered: {', '.join(available_handlers)}")
