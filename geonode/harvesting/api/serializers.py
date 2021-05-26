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

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from dynamic_rest.serializers import (
    DynamicModelSerializer,
    DynamicRelationField,
)
from rest_framework import (
    exceptions,
    serializers,
)
from rest_framework.fields import (
    get_error_detail,
    set_value,
    SkipField,
)
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings

from .. import (
    models,
    tasks,
    utils,
)

logger = logging.getLogger(__name__)


class CurrentUserDefault:
    requires_context = True

    def __call__(self, serializer_field):
        return serializer_field.context["request"].user


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
            "links",
        )

    default_owner = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
        default=CurrentUserDefault(),
    )
    links = serializers.SerializerMethodField()

    def get_links(self, obj):
        return {
            "self": reverse(
                "harvester-detail",
                kwargs={
                    "pk": obj.id,
                },
                request=self.context["request"],
            ),
            "harvestable-resources": reverse(
                "harvestable-resources-list",
                kwargs={
                    "harvester_id": obj.id,
                },
                request=self.context["request"],
            ),
        }


class HarvesterSerializer(BriefHarvesterSerializer):
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
            "links",
        )

    def create(self, validated_data):
        desired_status = validated_data.get("status", models.Harvester.STATUS_READY)
        if desired_status != models.Harvester.STATUS_READY:
            raise serializers.ValidationError(
                f"Invalid initial value for status: {desired_status!r}. "
                f"Either omit it or provide a "
                f"value of {models.Harvester.STATUS_READY!r}"
            )
        harvester = super().create(validated_data)
        available = utils.update_harvester_availability(harvester)
        if available:
            harvester.status = harvester.STATUS_UPDATING_HARVESTABLE_RESOURCES
            harvester.save()
            tasks.update_harvestable_resources.apply_async(args=(harvester.pk,))
        return harvester

    def update(self, instance: models.Harvester, validated_data):
        """Update the harvester instance and perform any required business logic as a side-effect.

        Updating the harvester's `status` attribute triggers additional work:

        - If `status` is set to
          `models.Harvester.STATUS_UPDATING_HARVESTABLE_RESOURCES, then we
          proceed to refresh all harvestable resources related to the harvester

        - If `status` is set to `models.Harvester.STATUS_PERFORM_HARVESTING
          then we proceed by starting a new harvesting session

        - If `status` is set to `models.Harvester.STATUS_CHECKING_AVAILABILITY
          then we proceed to check the availability of the remote service

        Note that all of these additional work items are carried out
        asynchronously via celery tasks.

        """

        desired_status = validated_data.get("status")
        ready = instance.status == models.Harvester.STATUS_READY
        if not ready:
            raise serializers.ValidationError(
                f"Harvester is currently busy. Please wait until current "
                f"status becomes {models.Harvester.STATUS_READY!r}"
            )
        elif desired_status == models.Harvester.STATUS_UPDATING_HARVESTABLE_RESOURCES:
            post_update_task = tasks.update_harvestable_resources.signature(args=(instance.id,))
        elif desired_status == models.Harvester.STATUS_PERFORMING_HARVESTING:
            post_update_task = tasks.harvesting_session_dispatcher.signature(args=(instance.id,))
        elif desired_status == models.Harvester.STATUS_CHECKING_AVAILABILITY:
            post_update_task = tasks.check_harvester_available.signature(args=(instance.id,))
        else:
            post_update_task = None
        update_result = super().update(instance, validated_data)
        if post_update_task is not None:
            post_update_task.apply_async()
        return update_result


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
            "status",
        ]

    def create(self, validated_data):
        # TODO: check if there is no other property being set other than `should_be_harvested`
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
