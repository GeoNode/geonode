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

from dynamic_rest.serializers import DynamicModelSerializer

from .. import models

logger = logging.getLogger(__name__)


class BriefHarvesterSerializer(DynamicModelSerializer):
    class Meta:
        model = models.Harvester
        fields = (
            "id",
            "name",
            "remote_url",
            "scheduling_enabled",
            "update_frequency",
        )


class HarvesterSerializer(DynamicModelSerializer):
    class Meta:
        model = models.Harvester
        fields = (
            "id",
            "name",
            "remote_url",
            "scheduling_enabled",
            "update_frequency",
            "default_owner",
            "default_access_permissions",
            "harvester_type",
            "harvester_type_specific_configuration",
        )


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
