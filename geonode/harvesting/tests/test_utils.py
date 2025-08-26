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
from django.conf import settings
from lxml import etree
from django.contrib.auth import get_user_model
from django.utils import timezone

from geonode.base.populate_test_data import create_single_dataset
from geonode.harvesting.models import HarvestableResource, Harvester
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.upload.handlers.remote.wms import create_harvestable_resource
from geonode.utils import get_xpath_value


class UtilsTestCase(GeoNodeBaseTestSupport):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service_url = f"{settings.GEOSERVER_LOCATION}ows"
        cls.user = get_user_model().objects.get(username="admin")
        cls.harvester, _ = Harvester.objects.get_or_create(
            remote_url=cls.service_url,
            name="harvester1",
            default_owner=cls.user,
            harvester_type="geonode.harvesting.harvesters.wms.OgcWmsHarvester",
        )
        cls.dataset = create_single_dataset(name="example_harvestable_resource")

    def test_get_xpath_value(self):
        fixtures = [
            (
                "<ns1:myElement xmlns:ns1='fake1' xmlns:ns2='fake2'><ns2:anotherElement>phony</ns2:anotherElement></ns1:myElement>",
                "/ns1:myElement/ns2:anotherElement",
                None,
                "phony",
            ),
            (
                "<ns1:myElement xmlns:ns1='fake1' xmlns:ns2='fake2'><ns2:anotherElement>phony</ns2:anotherElement></ns1:myElement>",
                "ns2:anotherElement",
                None,
                "phony",
            ),
            (
                "<ns1:myElement xmlns:ns1='fake1' xmlns:ns2='fake2' xmlns:ns3='fake3'><ns2:anotherElement><ns3:additional>phony</ns3:additional></ns2:anotherElement></ns1:myElement>",
                "ns2:anotherElement/ns3:additional",
                None,
                "phony",
            ),
        ]
        for element, xpath_expr, nsmap, expected in fixtures:
            xml_el = etree.fromstring(element)
            result = get_xpath_value(xml_el, xpath_expr, nsmap=nsmap)
            self.assertEqual(result, expected)

    def test_create_harvestable_resource(self):
        """
        Given a geonode resource and a service url, should link the
        harvestable resource with the harvester
        """

        # be sure that the dataset was not linked to the harvester
        try:
            self.assertFalse(HarvestableResource.objects.filter(geonode_resource=self.dataset).exists())

            result = create_harvestable_resource(self.dataset, self.service_url)
            # nothing is usually returned
            self.assertIsNone(result)

            # evaluating that the harvestable resource has been created
            hresource = HarvestableResource.objects.filter(geonode_resource=self.dataset).first()
            self.assertIsNotNone(hresource)
            self.assertEqual(hresource.geonode_resource.pk, self.dataset.pk)
        finally:
            HarvestableResource.objects.filter(geonode_resource=self.dataset).delete()

    def test_create_harvestable_resource_different_service_url(self):
        """
        Should ignore if the service url provided does not exists in the DB
        """
        with self.assertLogs(level="WARNING") as _log:
            create_harvestable_resource(self.dataset, "http://someurl.com")
        self.assertIn("The WMS layer does not belong to any known remote service", [x.message for x in _log.records])

    def test_create_harvestable_resource_on_existing_harvestable_resource(self):
        """
        If the harvestable resource already exists, it should link the newly created geonode resource
        with the harvestable resource, so the harvester will not harvest it again
        """
        try:
            self.__create_harvestable_resource()

            result = create_harvestable_resource(self.dataset, self.service_url)
            # nothing is usually returned
            self.assertIsNone(result)

            # evaluating that the harvestable resource has been created
            hresource = HarvestableResource.objects.filter(geonode_resource=self.dataset).first()
            self.assertIsNotNone(hresource)
            self.assertEqual(hresource.geonode_resource.pk, self.dataset.pk)
        finally:
            HarvestableResource.objects.filter(geonode_resource=self.dataset).delete()

    def test_create_harvestable_resource_different_geonode_resource(self):
        """
        If the harvestable resource already have geonode resource aligned, it should
        just ignore and log the information
        """
        try:
            self.__create_harvestable_resource(attach_resource=True)
            dataset2 = create_single_dataset("second dataset")
            dataset2.alternate = self.dataset.alternate
            dataset2.save()
            with self.assertLogs(level="WARNING") as _log:
                create_harvestable_resource(dataset2, self.service_url)
            self.assertIn(
                "The Resource assigned to the current HarvestableResource is different from the one provided, skipping...",
                [x.message for x in _log.records],
            )

        finally:
            HarvestableResource.objects.filter(geonode_resource=self.dataset).delete()

    def __create_harvestable_resource(self, attach_resource=False):
        HarvestableResource.objects.get_or_create(
            harvester=self.harvester,
            unique_identifier=self.dataset.alternate,
            geonode_resource=None if not attach_resource else self.dataset,
            title="Some title",
            defaults={
                "should_be_harvested": True,
                "remote_resource_type": self.dataset.resource_type,
                "last_updated": timezone.now(),
                "last_refreshed": timezone.now(),
                "last_harvested": timezone.now(),
                "last_harvesting_succeeded": True,
            },
        )
