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

import typing
import logging
import collections
import jsonschema.exceptions

from django.contrib.auth import get_user_model
from dynamic_rest.serializers import DynamicModelSerializer
from django.core.exceptions import ValidationError as DjangoValidationError
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
            "harvesting_session_update_frequency",
            "refresh_harvestable_resources_update_frequency",
            "check_availability_frequency",
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
            "harvestable_resources": reverse(
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
            "check_availability_frequency",
            "harvesting_session_update_frequency",
            "refresh_harvestable_resources_update_frequency",
            "default_owner",
            "harvester_type",
            "harvester_type_specific_configuration",
            "last_checked_availability",
            "last_checked_harvestable_resources",
            "last_check_harvestable_resources_message",
            "harvest_new_resources_by_default",
            "delete_orphan_resources_automatically",
            "last_updated",
            "links",
        )

    def validate(self, data):
        """Perform object-level validation

        In this method we implement validation of the following:

        - Check that the worker configuration is valid for the current worker type.
          This is done by validating the config against the worker's extra config
          jsonschema (if it exists)
        - Check that the client does not try to change the object's and worker config
          at the same time, as that could lead to invalid internal state (for example,
          if the worker config changes we need to regenerate the list of harvestable
          resources before allowing a new harvesting session to take place).

        """

        worker_config_field = "harvester_type_specific_configuration"
        worker_type_field = "harvester_type"
        worker_type = data.get(worker_type_field, getattr(self.instance, worker_type_field, None))
        worker_config = data.get(worker_config_field, getattr(self.instance, worker_config_field, None))
        if worker_type is not None and worker_config is not None:
            try:
                models.validate_worker_configuration(worker_type, worker_config)
            except jsonschema.exceptions.ValidationError:
                raise serializers.ValidationError(f"Invalid {worker_config_field!r} configuration")

        if data.get("status") and data.get(worker_config_field):
            raise serializers.ValidationError(
                f"Cannot update a harvester's 'status' and {worker_config_field!r} at " f"the same time"
            )
        return data

    def create(self, validated_data):
        desired_status = validated_data.get("status", models.Harvester.STATUS_READY)
        if desired_status != models.Harvester.STATUS_READY:
            raise serializers.ValidationError(
                f"Invalid initial value for status: {desired_status!r}. "
                f"Either omit it or provide a "
                f"value of {models.Harvester.STATUS_READY!r}"
            )
        return super().create(validated_data)

    def update(self, instance: models.Harvester, validated_data):
        """Update harvester and perform any required business logic as a side-effect.

        Updating the harvester's `status` attribute triggers additional work:

        - If `status` is set to
          `models.Harvester.STATUS_UPDATING_HARVESTABLE_RESOURCES`, then we
          proceed to refresh all harvestable resources related to the harvester

        - If `status` is set to `models.Harvester.STATUS_PERFORM_HARVESTING`
          then we proceed by starting a new harvesting session

        - If `status` is set to `models.Harvester.STATUS_CHECKING_AVAILABILITY`
          then we proceed to check the availability of the remote service

        Note that it is not possible for an API client to set a status of
        `models.Harvester.STATUS_READY`. This status is set internally.

        Additional work can also be triggered when a change to the harvester worker
        configuration is requested. In that case GeoNode must regenerate the list of
        harvestable resources.

        Also note that all of these additional work items are carried out
        asynchronously via celery tasks.

        """

        desired_status = validated_data.get("status")
        if not instance.status == models.Harvester.STATUS_READY:
            raise serializers.ValidationError(
                f"Harvester is currently busy. Please wait until current "
                f"status becomes {models.Harvester.STATUS_READY!r}"
            )
        elif desired_status == models.Harvester.STATUS_READY:
            raise serializers.ValidationError(
                f"Cannot set a status of {models.Harvester.STATUS_READY!r} explicitly. "
                f"This status can only be set by the server, when appropriate."
            )
        elif desired_status == models.Harvester.STATUS_UPDATING_HARVESTABLE_RESOURCES:
            session = models.AsynchronousHarvestingSession.objects.create(
                harvester=instance,
                session_type=models.AsynchronousHarvestingSession.TYPE_DISCOVER_HARVESTABLE_RESOURCES,
            )
            post_update_task = tasks.update_harvestable_resources.signature(args=(session.pk,))
        elif desired_status == models.Harvester.STATUS_PERFORMING_HARVESTING:
            session = models.AsynchronousHarvestingSession.objects.create(
                harvester=instance, session_type=models.AsynchronousHarvestingSession.TYPE_HARVESTING
            )
            post_update_task = tasks.harvesting_dispatcher.signature(args=(session.pk,))
        elif desired_status == models.Harvester.STATUS_CHECKING_AVAILABILITY:
            post_update_task = tasks.check_harvester_available.signature(args=(instance.id,))
        elif desired_status is None:
            current_worker_config = instance.harvester_type_specific_configuration
            desired_worker_config = validated_data.get("harvester_type_specific_configuration", current_worker_config)
            if desired_worker_config != current_worker_config:
                logger.debug(f"Regenerating harvestable resource list for harvester " f"{instance!r} asynchronously...")
                models.HarvestableResource.objects.filter(harvester=instance).delete()
                post_update_task = tasks.update_harvestable_resources.signature(args=(instance.id,))
            else:
                post_update_task = None
        else:
            post_update_task = None
        updated_instance = super().update(instance, validated_data)
        if post_update_task is not None:
            post_update_task.apply_async(args=(), expiration=30)
        return updated_instance


class BriefAsynchronousHarvestingSessionSerializer(DynamicModelSerializer):
    class Meta:
        model = models.AsynchronousHarvestingSession
        fields = (
            "id",
            "started",
            "updated",
            "ended",
            "total_records_to_process",
            "records_done",
        )


class HarvestableResourceSerializer(DynamicModelSerializer):
    class Meta:
        model = models.HarvestableResource
        fields = [
            "unique_identifier",
            "title",
            "should_be_harvested",
            "last_updated",
            "status",
            "remote_resource_type",
        ]
        read_only_fields = [
            "title",
            "last_updated",
            "status",
            "remote_resource_type",
        ]

    def create(self, validated_data):
        # NOTE: We are implementing `create()` rather than `update` intentionally, even if the
        # user is not allowed to create new records (check the `views.py` module) - the rationale
        # being that since we keep a harvestable_resource's `id` private it would be more involved
        # to deal with its update than with its creation. We are providing a custom `UpdateListModelMixin` class
        # that allows for bulk update of multiple instances simultaneously. This mixin class is instantiating
        # this serializer class without providing an instance and then calling its `save()` method
        harvestable_resource = models.HarvestableResource.objects.get(
            harvester=self.context["harvester"], unique_identifier=validated_data["unique_identifier"]
        )
        harvestable_resource.should_be_harvested = validated_data["should_be_harvested"]
        harvestable_resource.save()
        return harvestable_resource

    # TODO: need to check whether any worker-specific configuration has changed when the harvester is updated
    # if so, then we need to discard existing harvestable_resources and check them again

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
            message = self.error_messages["invalid"].format(datatype=type(data).__name__)
            raise exceptions.ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [message]}, code="invalid")

        ret = collections.OrderedDict()
        errors = collections.OrderedDict()
        fields = self._writable_fields

        for field in fields:
            validate_method = getattr(self, f"validate_{field.field_name}", None)
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
