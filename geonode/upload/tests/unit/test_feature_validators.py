#########################################################################
#
# Copyright (C) 2025 OSGeo
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

from geonode.tests.base import GeoNodeBaseTestSupport
from unittest.mock import patch, MagicMock
from django.core.exceptions import ValidationError
from geonode.upload.feature_validators import GeoserverFeatureValidator
from geonode.base.populate_test_data import create_single_dataset
from django.contrib.auth import get_user_model


class TestFeatureValidators(GeoNodeBaseTestSupport):

    def setUp(self):
        self.user = get_user_model().objects.create_user(username="testuser", password="testpassword")
        self.dataset = create_single_dataset(name="test_dataset", owner=self.user)

    @patch("geonode.geoserver.helpers.gs_catalog.get_resource")
    def test_handler_initialization(self, mock_get_resource):
        mock_feature_type = MagicMock()
        mock_feature_type.attributes_restrictions = {"attribute1": {"restrictions": {"enumeration": ["a", "b", "c"]}}}
        mock_get_resource.return_value = mock_feature_type

        handler = GeoserverFeatureValidator(self.dataset)

        self.assertEqual(len(handler.restrictions), 1)
        self.assertIn("attribute1", handler.restrictions)

    @patch("geonode.geoserver.helpers.gs_catalog.get_resource")
    def test_validate_valid_feature(self, mock_get_resource):
        mock_feature_type = MagicMock()
        mock_feature_type.attributes_restrictions = {
            "attribute1": {"restrictions": {"enumeration": ["a", "b", "c"]}},
            "attribute2": {"restrictions": {"range": {"min": 0, "max": 10}}},
        }
        mock_get_resource.return_value = mock_feature_type

        handler = GeoserverFeatureValidator(self.dataset)
        feature = {"attribute1": "a", "attribute2": 5}

        try:
            handler.validate(feature)
        except ValidationError:
            self.fail("Validation raised ValidationError unexpectedly!")

    @patch("geonode.geoserver.helpers.gs_catalog.get_resource")
    def test_validate_invalid_enumeration(self, mock_get_resource):
        mock_feature_type = MagicMock()
        mock_feature_type.attributes_restrictions = {"attribute1": {"restrictions": {"enumeration": ["a", "b", "c"]}}}
        mock_get_resource.return_value = mock_feature_type

        handler = GeoserverFeatureValidator(self.dataset)
        feature = {"attribute1": "d"}

        with self.assertRaises(ValidationError):
            handler.validate(feature)

    @patch("geonode.geoserver.helpers.gs_catalog.get_resource")
    def test_validate_invalid_range(self, mock_get_resource):
        mock_feature_type = MagicMock()
        mock_feature_type.attributes_restrictions = {"attribute2": {"restrictions": {"range": {"min": 0, "max": 10}}}}
        mock_get_resource.return_value = mock_feature_type

        handler = GeoserverFeatureValidator(self.dataset)
        feature = {"attribute2": 11}

        with self.assertRaises(ValidationError):
            handler.validate(feature)

    def test_validate_non_vector_dataset(self):
        self.dataset.subtype = "raster"
        self.dataset.save()

        handler = GeoserverFeatureValidator(self.dataset)
        feature = {"attribute1": "a"}

        try:
            handler.validate(feature)
        except ValidationError:
            self.fail("Validation raised ValidationError unexpectedly for non-vector dataset!")
