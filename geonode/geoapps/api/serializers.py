#########################################################################
#
# Copyright (C) 2020 OSGeo
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

from django.contrib.auth import get_user_model
from geonode.geoapps.api.exceptions import DuplicateGeoAppException, InvalidGeoAppException, GeneralGeoAppException

from geonode.geoapps.models import GeoApp
from geonode.resource.manager import resource_manager
from geonode.base.api.serializers import ResourceBaseSerializer

logger = logging.getLogger(__name__)


class GeoAppSerializer(ResourceBaseSerializer):
    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

    class Meta:
        model = GeoApp
        name = "geoapp"
        view_name = "geoapps-list"
        fields = list(set(ResourceBaseSerializer.Meta.fields + ("name",)))

    def extra_update_checks(self, validated_data):
        _user_profiles = {}
        for _key, _value in validated_data.items():
            if _key in ("owner", "poc", "metadata_owner"):
                _user_profiles[_key] = _value
        for _key, _value in _user_profiles.items():
            validated_data.pop(_key)
            _u = get_user_model().objects.filter(username=_value).first()
            if _u:
                validated_data[_key] = _u
            else:
                raise InvalidGeoAppException(f"The specified '{_key}' does not exist!")

    def extra_create_checks(self, validated_data):
        if "name" not in validated_data or "owner" not in validated_data:
            raise InvalidGeoAppException("No valid data: 'name' and 'owner' are mandatory fields!")

        if self.Meta.model.objects.filter(name=validated_data["name"]).count():
            raise DuplicateGeoAppException("A GeoApp with the same 'name' already exists!")

        self.extra_update_checks(validated_data)

    def _sanitize_validated_data(self, validated_data, instance=None):
        # Extract users' profiles
        _user_profiles = {}
        for _key, _value in validated_data.items():
            if _key in ("owner", "poc", "metadata_owner"):
                _user_profiles[_key] = _value
        for _key, _value in _user_profiles.items():
            validated_data.pop(_key)
            _u = get_user_model().objects.filter(username=_value).first()
            if _u:
                validated_data[_key] = _u
            else:
                raise InvalidGeoAppException(f"The specified '{_key}' does not exist!")

        return validated_data

    def _create_and_update(self, validated_data, instance=None):
        # Extract JSON blob
        _data = {}
        if "blob" in validated_data:
            _data = validated_data.pop("blob")

        # Create a new instance
        if not instance:
            _instance = resource_manager.create(None, resource_type=self.Meta.model, defaults=validated_data)
        else:
            _instance = instance

        try:
            self.Meta.model.objects.filter(pk=_instance.id).update(**validated_data)
            _instance.refresh_from_db()
        except Exception as e:
            raise GeneralGeoAppException(e)

        # Let's finalize the instance and notify the users
        validated_data["blob"] = _data
        return resource_manager.update(_instance.uuid, instance=_instance, vals=validated_data, notify=True)

    def create(self, validated_data):
        # Sanity checks
        _mandatory_fields = ["name", "owner", "resource_type"]
        if not all([_x in validated_data for _x in _mandatory_fields]):
            raise InvalidGeoAppException(f"No valid data: {_mandatory_fields} are mandatory fields!")

        if self.Meta.model.objects.filter(name=validated_data["name"]).count():
            raise DuplicateGeoAppException("A GeoApp with the same 'name' already exists!")

        return self._create_and_update(self._sanitize_validated_data(validated_data))

    def update(self, instance, validated_data):
        if instance.resource_type:
            validated_data["resource_type"] = instance.resource_type
        # Sanity checks
        _mandatory_fields = [
            "resource_type",
        ]
        if not all([_x in validated_data for _x in _mandatory_fields]):
            raise InvalidGeoAppException(f"No valid data: {_mandatory_fields} are mandatory fields!")

        return self._create_and_update(self._sanitize_validated_data(validated_data), instance=instance)
