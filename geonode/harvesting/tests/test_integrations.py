##############################################
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
import uuid
import datetime as dt
from unittest import mock

from django.test.utils import override_settings
from django.contrib.auth import get_user_model
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.layers.models import Dataset

from geonode.harvesting.resourcedescriptor import (
    RecordDescriptionContact,
    RecordDistribution,
    RecordIdentification,
    RecordDescription,
)
from geonode.harvesting.models import Harvester, HarvestableResource, AsynchronousHarvestingSession
from geonode.harvesting.harvesters.base import HarvestedResourceInfo
from geonode.harvesting.harvesters.geonodeharvester import GeonodeUnifiedHarvesterWorker


class HarvesterIntegrationsTestCase(GeoNodeBaseTestSupport):
    unique_identifier = "id"
    title = "Test"
    remote_url = "test.com"
    name = "This is a geonode harvester"
    user = get_user_model().objects.get(username="AnonymousUser")
    harvester_type = "geonode.harvesting.harvesters.geonodeharvester.GeonodeLegacyHarvester"

    @override_settings(ASYNC_SIGNALS=False)
    def setUp(self):
        super().setUp()

        self.record_description_contact = mock.MagicMock(RecordDescriptionContact)
        self.record_distribution = mock.MagicMock(RecordDistribution)
        self.record_distribution.thumbnail_url.return_value = "thumb.png"
        self.record_distribution.wms_url.return_value = "http://test.com/geoserver"
        self.record_identification = RecordIdentification(name=self.name, title=self.title, other_keywords=[])

        self.harvester = Harvester.objects.create(
            remote_url=self.remote_url, name=self.name, default_owner=self.user, harvester_type=self.harvester_type
        )
        self.harvestable_resource = HarvestableResource.objects.create(
            unique_identifier=self.unique_identifier,
            title=self.title,
            harvester=self.harvester,
            last_refreshed=dt.datetime.now(),
            remote_resource_type="dataset",
        )

        self.session = AsynchronousHarvestingSession.objects.create(
            harvester=self.harvester, session_type=AsynchronousHarvestingSession.TYPE_HARVESTING
        )

        self.record_description = RecordDescription(
            uuid=uuid.uuid4(),
            author=self.record_description_contact,
            date_stamp=dt.datetime.now(),
            distribution=self.record_distribution,
            identification=self.record_identification,
            point_of_contact=self.record_description_contact,
            reference_systems=["EPSG:3857"],
            additional_parameters={
                "alternate": "geonode:test",
                "workspace": "geonode",
                "subtype": "vector",
                "resource_type": "",
            },
        )

        self.harvested_info = HarvestedResourceInfo(
            resource_descriptor=self.record_description, copied_resources=[], additional_information=None
        )

    @mock.patch(
        "geonode.harvesting.harvesters.geonodeharvester.GeonodeCurrentHarvester.check_availability",
        mock.Mock(return_value=True),
    )
    def test_remote_subtype_is_set_for_harvested_dataset(self):
        worker = GeonodeUnifiedHarvesterWorker(remote_url=self.remote_url, harvester_id=self.harvester.id)
        worker.update_geonode_resource(self.harvested_info, self.harvestable_resource)
        dataset = Dataset.objects.get(alternate="geonode:test")
        self.assertEqual(dataset.subtype, "remote")
