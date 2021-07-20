#########################################################################
#
# Copyright (C) 2016 OSGeo
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
import xml.etree.ElementTree as ET

from django.db.models import Q
from django.test import RequestFactory
from geonode.layers.models import Dataset
from geonode.catalogue import get_catalogue
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.catalogue.models import catalogue_post_save

from geonode.catalogue.views import csw_global_dispatch
from geonode.layers.populate_datasets_data import create_dataset_data

from geonode.base.populate_test_data import (
    all_public,
    create_models,
    remove_models)

logger = logging.getLogger(__name__)


class CatalogueTest(GeoNodeBaseTestSupport):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_models(type=cls.get_type, integration=cls.get_integration)
        all_public()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        remove_models(cls.get_obj_ids, type=cls.get_type, integration=cls.get_integration)

    def setUp(self):
        super().setUp()
        self.request = self.__request_factory_single(123)
        create_dataset_data()
        self.user = "admin"
        self.passwd = "admin"

    def test_get_catalog(self):
        """Tests the get_catalogue function works."""
        c = get_catalogue()
        self.assertIsNotNone(c)

    def test_update_metadata_records(self):
        dataset = Dataset.objects.first()
        self.assertIsNotNone(dataset)
        dataset.abstract = "<p>Test HTML abstract</p>"
        dataset.save()
        self.assertEqual(dataset.abstract, "<p>Test HTML abstract</p>")
        self.assertEqual(dataset.raw_abstract, "Test HTML abstract")
        # refresh catalogue metadata records
        catalogue_post_save(instance=dataset, sender=dataset.__class__)
        # get all records
        csw = get_catalogue()
        record = csw.get_record(dataset.uuid)
        self.assertIsNotNone(record)
        self.assertEqual(record.identification.title, dataset.title)
        self.assertEqual(record.identification.abstract, dataset.raw_abstract)
        if len(record.identification.otherconstraints) > 0:
            self.assertEqual(record.identification.otherconstraints[0], dataset.raw_constraints_other)

    def test_given_a_simple_request_should_return_200(self):
        actual = csw_global_dispatch(self.request)
        self.assertEqual(200, actual.status_code)

    def test_given_a_request_for_a_single_dataset_should_return_single_value_in_xml_without_dataset_filter(self):
        dataset = Dataset.objects.first()
        request = self.__request_factory_single(dataset.uuid)
        response = csw_global_dispatch(request)
        root = ET.fromstring(response.content)
        actual = len(list(root))
        self.assertEqual(1, actual)

    def test_given_a_request_for_a_single_dataset_should_return_empty_value_in_xml_with_dataset_filter(self):
        dataset = Dataset.objects.first()
        request = self.__request_factory_single(dataset.uuid)
        response = csw_global_dispatch(request, self.dataset_filter)
        root = ET.fromstring(response.content)
        actual = len(list(root))
        self.assertEqual(0, actual)

    def test_given_a_request_for_multiple_dataset_should_return_empty_value_in_xml_with_dataset_filter(self):
        request = self.__request_factory_multiple()
        response = csw_global_dispatch(request, self.dataset_filter)
        root = ET.fromstring(response.content)
        actual = root.find("{http://www.opengis.net/cat/csw/2.0.2}SearchResults").attrib["numberOfRecordsReturned"]
        self.assertEqual(0, int(actual))

    def test_given_a_request_for_multiple_dataset_should_return_multiple_value_in_xml_with_dataset_filter(self):
        request = self.__request_factory_multiple()
        response = csw_global_dispatch(request, self.dataset_filter_multiple)
        root = ET.fromstring(response.content)
        actual = root.find("{http://www.opengis.net/cat/csw/2.0.2}SearchResults").attrib["numberOfRecordsReturned"]
        self.assertEqual(2, int(actual))

    @staticmethod
    def dataset_filter(dataset):
        return dataset.filter(uuid__startswith="foo_uuid")

    @staticmethod
    def dataset_filter_multiple(dataset):
        return dataset.filter(Q(title="CA") | Q(title="uniquetitle"))

    @staticmethod
    def __request_factory_single(uuid):
        factory = RequestFactory()
        url = "http://localhost:8000/catalogue/csw?request=GetRecordById"
        url += f"&service=CSW&version=2.0.2&id={uuid}"
        url += "&outputschema=http%3A%2F%2Fwww.isotc211.org%2F2005%2Fgmd&elementsetname=full"
        request = factory.get(url)

        request.user = AnonymousUser()
        return request

    @staticmethod
    def __request_factory_multiple():
        factory = RequestFactory()
        url = "http://localhost:8000/catalogue/csw/?request=GetRecords&service=CSW&version=2.0.2"
        url += "&outputschema=http%3A%2F%2Fwww.isotc211.org%2F2005%2Fgmd&elementsetname=full"
        url += "&typenames=gmd:MD_Metadata"
        request = factory.get(url)
        request.user = get_user_model().objects.first()
        return request
