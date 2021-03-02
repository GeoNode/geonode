# -*- coding: utf-8 -*-
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
from unittest.case import SkipTest
from geonode.layers.populate_layers_data import create_layer_data
from geonode.catalogue.views import csw_global_dispatch
import logging
from django.contrib.auth.models import AnonymousUser
from guardian.shortcuts import get_anonymous_user
import xml.etree.ElementTree as ET

from geonode.layers.models import Layer
from geonode.tests.base import GeoNodeBaseTestSupport
from django.test import RequestFactory
from geonode.catalogue import get_catalogue
from geonode.catalogue.models import catalogue_post_save

logger = logging.getLogger(__name__)


class CatalogueTest(GeoNodeBaseTestSupport):
    def setUp(self):
        super(CatalogueTest, self).setUp()

    def test_get_catalog(self):
        """Tests the get_catalogue function works."""

        c = get_catalogue()
        self.assertIsNotNone(c)

    def test_update_metadata_records(self):
        layer = Layer.objects.first()
        self.assertIsNotNone(layer)
        layer.abstract = "<p>Test HTML abstract</p>"
        layer.save()
        self.assertEqual(layer.abstract, "<p>Test HTML abstract</p>")
        self.assertEqual(layer.raw_abstract, "Test HTML abstract")
        # refresh catalogue metadata records
        catalogue_post_save(instance=layer, sender=layer.__class__)
        # get all records
        csw = get_catalogue()
        record = csw.get_record(layer.uuid)
        self.assertIsNotNone(record)
        self.assertEqual(record.identification.title, layer.title)
        self.assertEqual(record.identification.abstract, layer.raw_abstract)
        if len(record.identification.otherconstraints) > 0:
            self.assertEqual(record.identification.otherconstraints[0], layer.raw_constraints_other)


class TestCswGlobalDispatch(GeoNodeBaseTestSupport):
    def setUp(self):
        super(TestCswGlobalDispatch, self).setUp()
        self.request = self.__request_factory_single(123)
        create_layer_data()
        self.user = 'admin'
        self.passwd = 'admin'
        self.anonymous_user = get_anonymous_user()

    @SkipTest
    def test_given_a_simple_request_should_return_200(self):
        actual = csw_global_dispatch(self.request)
        self.assertEqual(200, actual.status_code)

    def test_given_a_request_for_a_single_uuid_should_return_single_value_in_xml(self):
        layer = Layer.objects.first()
        request = self.__request_factory_single(layer.uuid)
        response = csw_global_dispatch(request)
        root = ET.fromstring(response.content)
        actual = len(root.getchildren())
        self.assertEqual(1, actual)

    @staticmethod
    def __request_factory_single(uuid):
        factory = RequestFactory()
        request = factory.get(
            f"http://localhost:8000/catalogue/csw?request=GetRecordById&service=CSW&version=2.0.2&id={uuid}&outputschema=http%3A%2F%2Fwww.isotc211.org%2F2005%2Fgmd&elementsetname=full"
        )
        request.user = AnonymousUser()
        return request

    @staticmethod
    def __request_factory_multiple(uuid):
        factory = RequestFactory()
        request = factory.get(
            f"http://localhost:8000/catalogue/csw?request=GetRecordById&service=CSW&version=2.0.2&id={uuid}&outputschema=http%3A%2F%2Fwww.isotc211.org%2F2005%2Fgmd&elementsetname=full"
        )
        request.user = AnonymousUser()
        return request
