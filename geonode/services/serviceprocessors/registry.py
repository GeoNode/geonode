#########################################################################
#
# Copyright (C) 2026 OSGeo
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
from collections import OrderedDict

from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from geonode.services import enumerations


class ServiceTypeRegistry:
    def __init__(self):
        self.registry = OrderedDict()
        self._initialized = False

    def register(self, service_type, handler, label, OWS=False, **kwargs):
        self.registry[service_type] = {
            "OWS": OWS,
            "handler": handler,
            "label": label,
            **kwargs,
        }

    def unregister(self, service_type):
        self.registry.pop(service_type, None)

    def init_registry(self):
        if self._initialized:
            return

        self.registry = OrderedDict()
        self._register_default_service_types()
        self._register_configured_service_types()
        self._initialized = True

    def reset(self):
        self.registry = OrderedDict()
        self._initialized = False

    def get_available_service_types(self):
        self.init_registry()
        return OrderedDict(self.registry)

    def get_handler_class(self, service_type):
        service_type_config = self.get_available_service_types().get(service_type, {})
        handler = service_type_config.get("handler")
        if isinstance(handler, str):
            return import_string(handler)
        return handler

    def _register_default_service_types(self):
        # Keep imports lazy to avoid circular imports during Django app loading.
        from geonode.services.serviceprocessors.arcgis import ArcImageServiceHandler, ArcMapServiceHandler
        from geonode.services.serviceprocessors.wms import GeoNodeServiceHandler, WmsServiceHandler

        self.register(enumerations.WMS, WmsServiceHandler, _("Web Map Service"), OWS=True)
        self.register(enumerations.GN_WMS, GeoNodeServiceHandler, _("GeoNode (Web Map Service)"), OWS=True)
        self.register(enumerations.REST_MAP, ArcMapServiceHandler, _("ArcGIS REST MapServer"))
        self.register(enumerations.REST_IMG, ArcImageServiceHandler, _("ArcGIS REST ImageServer"))

    def _register_configured_service_types(self):
        for service_type_module_path in getattr(settings, "SERVICES_TYPE_MODULES", []):
            custom_service_type_module = import_string(service_type_module_path)
            for service_type, service_type_config in custom_service_type_module.services_type.items():
                self.register(service_type, **service_type_config)


service_type_registry = ServiceTypeRegistry()
