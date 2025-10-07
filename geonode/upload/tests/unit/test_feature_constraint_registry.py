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

from django.test import override_settings
from geonode.tests.base import GeoNodeBaseTestSupport
from unittest.mock import patch, MagicMock
from geonode.upload.registry import FeatureConstraintRegistry
from geonode.upload.feature_constraint_handlers import GeoserverFeatureConstraintHandler, BaseFeatureConstraintHandler


class AnotherMockHandler(BaseFeatureConstraintHandler):
    def __init__(self, dataset):
        super().__init__(dataset)

    def validate(self, feature):
        pass


@override_settings(
    FEATURE_CONSTRAINT_HANDLERS=["geonode.upload.feature_constraint_handlers.GeoserverFeatureConstraintHandler"]
)
class TestFeatureConstraintRegistry(GeoNodeBaseTestSupport):

    def setUp(self):
        self.registry = FeatureConstraintRegistry()
        self.registry.init_registry()

    def tearDown(self):
        self.registry.reset()

    def test_init_registry(self):
        self.assertEqual(len(self.registry.REGISTRY), 1)
        self.assertEqual(self.registry.REGISTRY[0], GeoserverFeatureConstraintHandler)

    def test_add_remove_handler(self):
        self.registry.add("geonode.upload.tests.unit.test_feature_constraint_registry.AnotherMockHandler")
        self.assertEqual(len(self.registry.REGISTRY), 2)
        self.assertIn(AnotherMockHandler, self.registry.REGISTRY)

        self.registry.remove("geonode.upload.tests.unit.test_feature_constraint_registry.AnotherMockHandler")
        self.assertEqual(len(self.registry.REGISTRY), 1)
        self.assertNotIn(AnotherMockHandler, self.registry.REGISTRY)

    def test_reset_registry(self):
        self.registry.add("geonode.upload.tests.unit.test_feature_constraint_registry.AnotherMockHandler")
        self.assertEqual(len(self.registry.REGISTRY), 2)

        self.registry.reset()
        self.assertEqual(len(self.registry.REGISTRY), 0)
        self.assertEqual(len(self.registry.HANDLERS), 0)

    @patch("geonode.upload.feature_constraint_handlers.gs_catalog.get_resource")
    def test_init_handlers_initializes_once(self, mock_get_resource):
        mock_dataset = MagicMock()
        mock_dataset.subtype = "vector"

        self.registry.init_handlers(mock_dataset)

        self.assertEqual(len(self.registry.HANDLERS), 1)
        self.assertIsInstance(self.registry.HANDLERS[0], GeoserverFeatureConstraintHandler)
        self.assertEqual(self.registry.HANDLERS[0].dataset, mock_dataset)

        # Assert that get_resource was called only once during init_handlers
        mock_get_resource.assert_called_once()

        # Create a second feature and validate it
        mock_feature = {"attr1": "val1"}
        self.registry.validate(mock_feature)

        # Assert that get_resource is still called only once
        mock_get_resource.assert_called_once()

    @patch.object(GeoserverFeatureConstraintHandler, "validate")
    def test_validate_calls_handler(self, mock_validate):
        mock_dataset = MagicMock()
        mock_feature = {}
        self.registry.init_handlers(mock_dataset)
        self.registry.validate(mock_feature)
        mock_validate.assert_called_once_with(mock_feature)
