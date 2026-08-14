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
from geonode.maps.models import Map


class MapResourceManager(BaseResourceManager):
    handled_model = Map

    def _post_change_routines(
        self, instance: Map, create_action_perfomed: bool, additional_data: dict = None, notify: bool = True
    ):
        additional_data = additional_data or {}

        if not create_action_perfomed:
            from geonode.maps.signals import map_changed_signal

            dataset_names_before_changes = additional_data.pop("dataset_names_before_changes", [])
            dataset_names_after_changes = [lyr.alternate for lyr in instance.datasets]
            if dataset_names_before_changes != dataset_names_after_changes:
                map_changed_signal.send_robust(sender=instance, what_changed="datasets")

        return super().update(instance.uuid, instance=instance, notify=notify)

    def create(
        self, uuid: str, /, resource_type: typing.Optional[object] = None, defaults: dict = {}, **kwargs
    ) -> ResourceBase:
        notify = kwargs.pop("notify", True)
        request_user = kwargs.get("user")
        payload = copy.deepcopy(defaults or {})
        extent = payload.pop("extent", None)
        post_creation_data = {"thumbnail": payload.pop("thumbnail_url", "")}
        maplayers = payload.pop("maplayers", None)
        instance = super().create(uuid, resource_type=resource_type or Map, defaults=payload)

        if maplayers is not None:
            instance.maplayers.set(maplayers)
            instance.refresh_from_db()

        if extent is not None or request_user:
            self._apply_extent_and_role_defaults(instance, extent=extent, user=request_user)

        instance = self._post_change_routines(
            instance=instance,
            create_action_perfomed=True,
            additional_data=post_creation_data,
            notify=notify,
        )
        self.set_thumbnail(instance.uuid, instance=instance, overwrite=False)
        return instance

    def update(self, uuid: str, /, instance: ResourceBase = None, vals: dict = {}, **kwargs) -> ResourceBase:
        dataset_names_before_changes = kwargs.pop("dataset_names_before_changes", None)
        notify = kwargs.pop("notify", True)

        payload = copy.deepcopy(vals or {})
        extent = payload.pop("extent", None)
        request_user = kwargs.get("user")
        post_change_data = {
            "thumbnail": payload.pop("thumbnail_url", ""),
            "dataset_names_before_changes": dataset_names_before_changes or [],
        }
        maplayers = payload.pop("maplayers", None)

        instance = super().update(uuid, instance=instance, vals=payload, notify=False, **kwargs)

        if maplayers is not None:
            instance.maplayers.set(maplayers)
            instance.refresh_from_db()

        if extent or request_user:
            # Mirrors ResourceBaseSerializer.save() (extent + role defaults); could be moved to the API,
            # but it’s kept here to centralize manager behavior.
            self._apply_extent_and_role_defaults(instance, extent=extent, user=request_user)

        instance = self._post_change_routines(
            instance=instance,
            create_action_perfomed=False,
            additional_data=post_change_data,
            notify=notify,
        )
        return instance
