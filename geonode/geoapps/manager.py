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

from geonode.base.models import ResourceBase
from geonode.resource.manager import BaseResourceManager
from geonode.geoapps.models import GeoApp


class GeoAppResourceManager(BaseResourceManager):
    handled_model = GeoApp

    def _create_and_update(self, payload, instance=None, notify: bool = True):
        from geonode.geoapps.api.exceptions import GeneralGeoAppException

        payload = copy.deepcopy(payload)
        blob = payload.pop("blob", {})

        if not instance:
            instance = super().create(None, resource_type=GeoApp, defaults=payload)

        try:
            GeoApp.objects.filter(pk=instance.id).update(**payload)
            instance.refresh_from_db()
        except Exception as e:
            raise GeneralGeoAppException(e)

        payload["blob"] = blob
        return super().update(instance.uuid, instance=instance, vals=payload, notify=notify)

    def create(
        self, uuid: str, /, resource_type: typing.Optional[object] = None, defaults: dict = {}, **kwargs
    ) -> ResourceBase:
        notify = kwargs.pop("notify", True)
        payload = copy.deepcopy(defaults or {})
        return self._create_and_update(payload, notify=notify)

    def update(self, uuid: str, /, instance: ResourceBase = None, vals: dict = {}, **kwargs) -> ResourceBase:
        notify = kwargs.pop("notify", True)
        payload = vals or {}
        if payload:
            return self._create_and_update(payload, instance=instance, notify=notify)
        return super().update(uuid, instance=instance, vals=vals, notify=notify, **kwargs)
