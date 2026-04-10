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

import copy
import typing
import logging

from geonode.base.models import ResourceBase
from geonode.resource.manager import BaseResourceManager
from geonode.geoapps.models import GeoApp

logger = logging.getLogger(__name__)


class GeoAppResourceManager(BaseResourceManager):
    handled_model = GeoApp

    def _create_and_update(self, payload, instance=None, notify: bool = True, request_user=None):
        from geonode.geoapps.api.exceptions import GeneralGeoAppException

        payload = copy.deepcopy(payload)
        extent = payload.pop("extent", None)
        blob = payload.pop("blob", {})

        created = False
        if not instance:
            instance = super().create(None, resource_type=GeoApp, defaults=payload)
            created = True

        if created and "owner" in payload:
            payload["owner"] = instance.owner

        try:
            GeoApp.objects.filter(pk=instance.id).update(**payload)
            instance.refresh_from_db()
        except Exception as e:
            logger.exception(f"Error while creating or updating GeoApp instance with exception {e}")
            raise GeneralGeoAppException("An error occurred while saving the GeoApp.")

        payload["blob"] = blob
        instance = super().update(instance.uuid, instance=instance, vals=payload, notify=notify)
        if extent or request_user:
            # Mirrors ResourceBaseSerializer.save() (extent + role defaults); could be moved to the API,
            # but it’s kept here to centralize manager behavior.
            self._apply_extent_and_role_defaults(instance, extent=extent, user=request_user)
        return instance

    def create(
        self, uuid: str, /, resource_type: typing.Optional[object] = None, defaults: dict = {}, **kwargs
    ) -> ResourceBase:
        notify = kwargs.pop("notify", True)
        request_user = kwargs.get("user")
        payload = copy.deepcopy(defaults or {})
        return self._create_and_update(payload, notify=notify, request_user=request_user)

    def update(self, uuid: str, /, instance: ResourceBase = None, vals: dict = {}, **kwargs) -> ResourceBase:
        notify = kwargs.pop("notify", True)
        request_user = kwargs.get("user")
        payload = vals or {}
        if payload:
            return self._create_and_update(payload, instance=instance, notify=notify, request_user=request_user)
        return super().update(uuid, instance=instance, vals=vals, notify=notify, **kwargs)
