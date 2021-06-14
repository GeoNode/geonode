# -*- coding: utf-8 -*-
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
from geonode.base.models import ResourceBase
import json
import logging

from django.contrib.auth import get_user_model
from dynamic_rest.fields.fields import DynamicRelationField
from dynamic_rest.serializers import DynamicModelSerializer
from geonode.base.api.serializers import ResourceBaseSerializer
from geonode.geoapps.models import GeoApp
from rest_framework.serializers import ValidationError

logger = logging.getLogger(__name__)


class GeoAppDataField(DynamicRelationField):

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)


class GeoAppDataSerializer(DynamicModelSerializer):

    class Meta:
        ref_name = 'GeoAppData'
        model = ResourceBase
        name = 'GeoAppData'
        fields = ('pk', 'blob')
       
    def to_representation(self, value):
        data = GeoApp.objects.filter(resourcebase_ptr_id=value)
        if data.exists():
            return data.first().data
        return {}


class GeoAppSerializer(ResourceBaseSerializer):
    """
     - Deferred / not Embedded --> ?include[]=data
    """
    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super(GeoAppSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = GeoApp
        name = 'geoapp'
        view_name = 'geoapps-list'
        fields = (
            'pk', 'uuid',
            'zoom', 'projection', 'center_x', 'center_y',
            'urlsuffix', 'data'
        )

    def to_internal_value(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        if 'data' in data:
            _data = data.pop('data')
            if self.is_valid():
                data['blob'] = _data

        return data

    def extra_update_checks(self, validated_data):
        _user_profiles = {}
        for _key, _value in validated_data.items():
            if _key in ('owner', 'poc', 'metadata_owner'):
                _user_profiles[_key] = _value
        for _key, _value in _user_profiles.items():
            validated_data.pop(_key)
            _u = get_user_model().objects.filter(username=_value).first()
            if _u:
                validated_data[_key] = _u
            else:
                raise ValidationError(f"The specified '{_key}' does not exist!")

    def extra_create_checks(self, validated_data):
        if 'name' not in validated_data or \
                'owner' not in validated_data:
            raise ValidationError("No valid data: 'name' and 'owner' are mandatory fields!")

        if self.Meta.model.objects.filter(name=validated_data['name']).count():
            raise ValidationError("A GeoApp with the same 'name' already exists!")

        self.extra_update_checks(validated_data)

    def create(self, validated_data):

        return _instance

    def update(self, instance, validated_data):

        # perform sanity checks
        self.extra_update_checks(validated_data)

        # Extract JSON blob
        _data = None
        if 'blob' in validated_data:
            _data = validated_data.pop('blob')

        try:
            self.Meta.model.objects.filter(pk=instance.id).update(**validated_data)
            instance.refresh_from_db()
        except Exception as e:
            raise ValidationError(e)

        if instance and _data:
            try:
                _geo_app, _created = GeoAppData.objects.get_or_create(resource=instance)
                _geo_app.blob = _data
                _geo_app.save()
            except Exception as e:
                raise ValidationError(e)

        instance.save()
        return instance
