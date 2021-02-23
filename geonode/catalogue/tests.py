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
import logging

from geonode.layers.models import Layer
from geonode.tests.base import GeoNodeBaseTestSupport

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
            self.assertEqual(
                record.identification.otherconstraints[0],
                layer.raw_constraints_other)
