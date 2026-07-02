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
import logging
import hashlib
import json

from collections import OrderedDict
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from geonode.services import enumerations
from geonode.services.utils import parse_services_types
from django.core.cache import caches

service_cache = caches["services"]
logger = logging.getLogger(__name__)


def _build_auth_cache_fingerprint(auth=None, auth_config=None):
    if auth_config is not None:
        auth_identity = {
            "type": getattr(auth_config, "type", None),
            "payload": getattr(auth_config, "payload", None),
        }
    elif auth is not None:
        if isinstance(auth, tuple) and len(auth) == 2:
            auth_identity = {"type": "basic", "payload": {"username": auth[0], "password": auth[1]}}
        elif hasattr(auth, "username") and hasattr(auth, "password"):
            auth_identity = {
                "type": auth.__class__.__name__,
                "payload": {"username": auth.username, "password": auth.password},
            }
        else:
            auth_identity = repr(auth)
    else:
        return "-"

    encoded = json.dumps(auth_identity, sort_keys=True, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def get_service_cache_key(base_url, service_type=enumerations.AUTO, service_id=None, auth=None, auth_config=None):
    auth_fingerprint = _build_auth_cache_fingerprint(auth=auth, auth_config=auth_config)
    return f"{service_type}|{service_id or '-'}|{auth_fingerprint}|{base_url}"


def get_available_service_types():
    # LGTM: Fixes - Module uses member of cyclically imported module, which can lead to failure at import time.
    from geonode.services.serviceprocessors.wms import GeoNodeServiceHandler, WmsServiceHandler
    from geonode.services.serviceprocessors.arcgis import ArcImageServiceHandler, ArcMapServiceHandler

    default = OrderedDict(
        {
            enumerations.WMS: {"OWS": True, "handler": WmsServiceHandler, "label": _("Web Map Service")},
            enumerations.GN_WMS: {
                "OWS": True,
                "handler": GeoNodeServiceHandler,
                "label": _("GeoNode (Web Map Service)"),
            },
            # enumerations.WFS: {"OWS": True, "handler": ServiceHandlerBase, "label": _('Paired WMS/WFS/WCS'),
            # enumerations.TMS: {"OWS": False, "handler": ServiceHandlerBase, "label": _('Paired WMS/WFS/WCS'),
            enumerations.REST_MAP: {"OWS": False, "handler": ArcMapServiceHandler, "label": _("ArcGIS REST MapServer")},
            enumerations.REST_IMG: {
                "OWS": False,
                "handler": ArcImageServiceHandler,
                "label": _("ArcGIS REST ImageServer"),
            },
            # enumerations.CSW: {"OWS": False, "handler": ServiceHandlerBase, "label": _('Catalogue Service')},
            # enumerations.OGP: {"OWS": True, "handler": ServiceHandlerBase, "label": _('OpenGeoPortal')},  # TODO: verify this
            # enumerations.HGL: {"OWS": False, "handler": ServiceHandlerBase, "label": _('Harvard Geospatial Library')},  # TODO: verify this
        }
    )

    return OrderedDict({**default, **parse_services_types()})


def get_service_handler(base_url, service_type=enumerations.AUTO, service_id=None, *args, **kwargs):
    """Return the appropriate remote service handler for the input URL.
    If the service type is not explicitly passed in it will be guessed from
    """

    cache_key = get_service_cache_key(
        base_url,
        service_type=service_type,
        service_id=service_id,
        auth=kwargs.get("auth"),
        auth_config=kwargs.get("auth_config"),
    )

    if entry := service_cache.get(cache_key):
        return entry

    handlers = get_available_service_types()

    handler = handlers.get(service_type, {}).get("handler")
    try:
        service_handler = handler(base_url, service_id, *args, **kwargs)
        service_cache.set(cache_key, service_handler, settings.SERVICE_CACHE_EXPIRATION_TIME)
    except Exception as e:
        logger.exception(e)
        logger.exception(msg=f"Could not parse service {base_url}")
        raise
    return service_handler
