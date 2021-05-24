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

import logging
import typing

from dynamic_rest.serializers import (
    DynamicEphemeralSerializer,
    DynamicModelSerializer,
)
from rest_framework import serializers

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


# class HarvestableResourceSerializer(DynamicEphemeralSerializer):
class HarvestableResourceSerializer(serializers.Serializer):
    """
    Works with a mixed set of models.HarvestableResource and just resources retrieved
    on the fly from the remote
    """

    unique_identifier = serializers.CharField(max_length=255)
    title = serializers.CharField(max_length=255, read_only=True)
    should_be_harvested = serializers.BooleanField(default=False)

    def to_representation(self, resource: BriefRemoteResource):
        representation = super().to_representation(resource)
        representation["should_be_harvested"] = False
        return representation

    def create(self, validated_data):
        logger.debug("inside serializer update method for instance")
        logger.debug(f"validated_data: {validated_data}")
        logger.debug(f"context of the instance serializer: {self.context}")
        unique_id = None  # TODO: harvester worker needs to generate this from validated_data
        resource_exists = models.HarvestableResource.objects.filter(
            harvester=self.context["harvester"], unique_identifier=unique_id).exists()
        if resource_exists and validated_data["should_be_harvested"]:
            pass  # nothing to do, resource already marked for harvesting
        elif resource_exists:  # need to delete the resource
            num_deleted, deleted_types = models.HarvestableResource.objects.filter(
                harvester=self.context["harvester"],
                unique_identifier=unique_id
            ).delete()
        elif not resource_exists and validated_data["should_be_harvested"]:
            # create the resource
            resource = models.HarvestableResource.objects.create(
                unique_identifier=unique_id, harvester=self.context["harvester"])
        else:
            pass  # nothing to do, the resource does not exist and the user doesn't want it to be harvested

        harvestable_resource, created = models.HarvestableResource.objects.get_or_create(
            unique_identifier=validated_data["unique_identifier"],
            harvester=self.context["harvester"],
            defaults={
                "should_be_harvested": self.context["should_be_harvested"]
            }
        )


# class HarvestableResourceListSerializer(DynamicEphemeralSerializer):
class HarvestableResourceListSerializer(serializers.Serializer):
    resources = HarvestableResourceSerializer(many=True)

    def create(self, validated_data):
        logger.debug("inside serializer create method for list")
        logger.debug(f"validated_data: {validated_data}")
        logger.debug(f"validated unique_identifier: {validated_data['resources'][0]['unique_identifier']}")
        logger.debug(f"context of the list serializer: {self.context}")
        for raw_resource in validated_data["resources"]:
            serialized = HarvestableResourceSerializer(
                data=raw_resource, context=self.context)
            serialized.is_valid(raise_exception=True)
            serialized.save()
        return {}
