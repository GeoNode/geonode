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

from collections import OrderedDict
from django.utils.translation import ugettext as _

from geonode.services import enumerations
from geonode.services.utils import parse_services_types

logger = logging.getLogger(__name__)


def get_available_service_types():
    # LGTM: Fixes - Module uses member of cyclically imported module, which can lead to failure at import time.
    from geonode.services.serviceprocessors.wms import GeoNodeServiceHandler, WmsServiceHandler
    from geonode.services.serviceprocessors.arcgis import ArcImageServiceHandler, ArcMapServiceHandler

    default = OrderedDict({
        enumerations.WMS: {"OWS": True, "handler": WmsServiceHandler, "label": _('Web Map Service')},
        enumerations.GN_WMS: {"OWS": True, "handler": GeoNodeServiceHandler, "label": _('GeoNode (Web Map Service)')},
        # enumerations.WFS: {"OWS": True, "handler": ServiceHandlerBase, "label": _('Paired WMS/WFS/WCS'},
        # enumerations.TMS: {"OWS": False, "handler": ServiceHandlerBase, "label": _('Paired WMS/WFS/WCS'},
        enumerations.REST_MAP: {"OWS": False, "handler": ArcMapServiceHandler, "label": _('ArcGIS REST MapServer')},
        enumerations.REST_IMG: {"OWS": False, "handler": ArcImageServiceHandler, "label": _('ArcGIS REST ImageServer')},
        # enumerations.CSW: {"OWS": False, "handler": ServiceHandlerBase, "label": _('Catalogue Service')},
        # enumerations.OGP: {"OWS": True, "handler": ServiceHandlerBase, "label": _('OpenGeoPortal')},  # TODO: verify this
        # enumerations.HGL: {"OWS": False, "handler": ServiceHandlerBase, "label": _('Harvard Geospatial Library')},  # TODO: verify this
    })

    return OrderedDict({**default, **parse_services_types()})


def get_service_handler(base_url, service_type=enumerations.AUTO):
    """Return the appropriate remote service handler for the input URL.
    If the service type is not explicitly passed in it will be guessed from
    """
    handlers = get_available_service_types()

    handler = handlers.get(service_type, {}).get("handler")
    try:
        service = handler(base_url)
    except Exception:
        logger.exception(
            msg=f"Could not parse service {base_url}")
        raise
    return service
