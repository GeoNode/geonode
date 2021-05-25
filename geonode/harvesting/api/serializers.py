#########################################################################
#
# Copyright (C) 2021 OSGeo
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

import collections
import logging
import typing

from django.core.exceptions import ValidationError as DjangoValidationError
from dynamic_rest.serializers import DynamicModelSerializer
from rest_framework import exceptions
from rest_framework.settings import api_settings
from rest_framework.fields import (
    get_error_detail,
    set_value,
    SkipField,
)

from .. import (
    models,
    tasks,
    utils,
)
from ..harvesters.base import BriefRemoteResource

logger = logging.getLogger(__name__)


class BriefHarvesterSerializer(DynamicModelSerializer):
    class Meta:
        model = models.Harvester
        fields = (
            "id",
            "name",
            "status",
            "remote_url",
            "remote_available",
            "scheduling_enabled",
            "update_frequency",
            "default_owner",
        )


class HarvesterSerializer(DynamicModelSerializer):
    class Meta:
        model = models.Harvester
        fields = (
            "id",
            "name",
            "status",
            "remote_url",
            "remote_available",
            "scheduling_enabled",
            "update_frequency",
            "default_owner",
            "default_access_permissions",
            "harvester_type",
            "harvester_type_specific_configuration",
            "update_frequency",
            "check_availability_frequency",
            "last_checked_availability",
            "last_checked_harvestable_resources",
            "last_check_harvestable_resources_message",
            "harvest_new_resources_by_default",
            "delete_orphan_resources_automatically",
            "last_updated",
        )

    def create(self, validated_data):
        harvester = super().create(validated_data)
        available = utils.update_harvester_availability(harvester)
        if available:
            tasks.update_harvestable_resources.apply_async(args=(harvester.pk,))
        return harvester


class BriefHarvestingSessionSerializer(DynamicModelSerializer):
    class Meta:
        model = models.HarvestingSession
        fields = (
            "id",
            "started",
            "updated",
            "ended",
            "records_harvested",
        )


class HarvestableResourceSerializer(DynamicModelSerializer):

    class Meta:
        model = models.HarvestableResource
        fields = [
            "unique_identifier",
            "title",
            "should_be_harvested",
            "available",
            "last_updated",
        ]

    def create(self, validated_data):
        harvestable_resource = models.HarvestableResource.objects.get(
            harvester=self.context["harvester"],
            unique_identifier=validated_data["unique_identifier"]
        )
        harvestable_resource.should_be_harvested = (
            validated_data["should_be_harvested"])
        harvestable_resource.save()
        return harvestable_resource

    def to_internal_value(self, data):
        """Verbatim copy of the original drf `to_internal_value()` method.

        This method replicates the implementation found on
        `restframework.serializers.Serializer.to_internal_value` method because the
        dynamic-rest package (which we are using, and which overrides the base
        implementation) adds some custom stuff on top of it which depends on the input
        data containing the instance's `id` property, which we are not requiring.

        A HarvestableResource's `id` is an implementation detail that is not exposed
        publicly. We rely on the instance's `unique_identifier` instead.

        """

        if not isinstance(data, typing.Mapping):
            message = self.error_messages['invalid'].format(
                datatype=type(data).__name__
            )
            raise exceptions.ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [message]
            }, code='invalid')

        ret = collections.OrderedDict()
        errors = collections.OrderedDict()
        fields = self._writable_fields

        for field in fields:
            validate_method = getattr(self, 'validate_' + field.field_name, None)
            primitive_value = field.get_value(data)
            try:
                validated_value = field.run_validation(primitive_value)
                if validate_method is not None:
                    validated_value = validate_method(validated_value)
            except exceptions.ValidationError as exc:
                errors[field.field_name] = exc.detail
            except DjangoValidationError as exc:
                errors[field.field_name] = get_error_detail(exc)
            except SkipField:
                pass
            else:
                set_value(ret, field.source_attrs, validated_value)

        if errors:
            raise exceptions.ValidationError(errors)

        return ret
