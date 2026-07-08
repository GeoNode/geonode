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

from geonode.services import enumerations
from geonode.services.serviceprocessors.cache import service_handler_cache
from geonode.services.serviceprocessors.registry import service_type_registry

logger = logging.getLogger(__name__)


def get_service_cache_key(base_url, service_type=enumerations.AUTO, service_id=None, auth=None, auth_config=None):
    return service_handler_cache.get_key(
        base_url, service_type=service_type, service_id=service_id, auth=auth, auth_config=auth_config
    )


def get_available_service_types():
    return service_type_registry.get_available_service_types()


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

    if entry := service_handler_cache.get(cache_key):
        return entry

    handler = service_type_registry.get_handler_class(service_type)
    try:
        service_handler = handler(base_url, service_id, *args, **kwargs)
        service_handler_cache.set(cache_key, service_handler)
    except Exception as e:
        logger.exception(e)
        logger.exception(msg=f"Could not parse service {base_url}")
        raise
    return service_handler
