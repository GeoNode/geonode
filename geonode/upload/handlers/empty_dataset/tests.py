#########################################################################
#
# Copyright (C) 2024 OSGeo
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
from collections import namedtuple
from unittest.mock import MagicMock
from django.test import TestCase
from geonode.resource.models import ExecutionRequest
from geonode.upload.handlers.empty_dataset.handler import EmptyDatasetHandler
from django.contrib.auth import get_user_model
from geonode.base.populate_test_data import create_single_dataset
from geonode.upload.handlers.empty_dataset.utils import add_attributes_to_xml, validate_attributes, base_xml


class FakeObj:
    name = "GeoNode"
    status_code = 201

    def raise_for_status(self):
        return


class TestEmptyDatasetHandler(TestCase):
    databases = ("default", "datastore")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = EmptyDatasetHandler()
        cls.user, _ = get_user_model().objects.get_or_create(username="admin")
        cls.owner = get_user_model().objects.first()
        cls.layer = create_single_dataset(name="empty_dataset", owner=cls.owner)
        cls.attributes = {
            "field_str": {"type": "string"},
            "field_int": {"type": "integer"},
            "field_date": {"type": "date"},
            "field_float": {"type": "float"},
            "field_str_options": {"type": "string", "nillable": False, "options": ["A", "B", "C"]},
            "field_int_options": {"type": "integer", "nillable": False, "options": [1, 2, 3]},
            "field_int_range": {"type": "integer", "nillable": False, "range": {"min": 1, "max": 10}},
            "field_float_options": {"type": "float", "nillable": False, "options": [1.2, 2.4, 3.6]},
            "field_float_range": {"type": "float", "nillable": False, "range": {"min": 1.5, "max": 10.5}},
        }

    def test_supported_file_extension_config_should_be_empty(self):
        """
        Config should not be exposed to be listed in the upload panel
        """
        self.assertDictEqual(self.handler.supported_file_extension_config, {})

    def test_can_handle(self):
        """
        Should be true if the is_empty key is passed in the payload, false if not
        """
        payload = {"is_empty": True}
        self.assertTrue(self.handler.can_handle(payload))
        payload = {"is_empty": False}
        self.assertFalse(self.handler.can_handle(payload))
        payload = {"base_file": "some file"}
        self.assertFalse(self.handler.can_handle(payload))

    def test_can_do(self):
        """
        Handler should return True if can do the CREATE operation but not the UPLOAD
        """
        self.assertTrue(self.handler.can_do("create"))
        self.assertFalse(self.handler.can_do("upload"))

    def test_has_serializer(self):
        """
        Should retrun the serializer if the attributes are present and if is a create operation
        """
        payload = {"attributes": "some attributes", "action": "create"}
        self.assertIsNotNone(self.handler.has_serializer(payload))
        payload = {"attributes": "some attributes", "action": "upload"}
        self.assertIsNone(self.handler.has_serializer(payload))
        payload = {"action": "create"}
        self.assertIsNone(self.handler.has_serializer(payload))

    def test_is_valid(self):
        """
        Should be true if the payload is correct as expected
        """
        try:
            exec_req = ExecutionRequest.objects.create(
                user=self.user,
                func_name="test",
                input_params={
                    "geom": "Geometry",
                    "title": "Geometry",
                    "attributes": {
                        "field_str": {"type": "string"},
                        "field_int": {"type": "integer"},
                    },
                    "is_empty": True,
                },
            )

            self.assertTrue(self.handler.is_valid({}, self.user, execution_id=str(exec_req.exec_id)))
        finally:
            if exec_req:
                exec_req.delete()

    def test_is_valid_is_false(self):
        """
        Should be false if the payload is not as expected
        """
        try:
            exec_req = ExecutionRequest.objects.create(
                user=self.user,
                func_name="test",
                input_params={
                    "geom": "Geometry",
                    "title": "Geometry",
                    "is_empty": True,
                },
            )
            with self.assertRaises(Exception):
                self.handler.is_valid({}, self.user, execution_id=str(exec_req.exec_id))
        finally:
            if exec_req:
                exec_req.delete()

    def test__define_dynamic_layer_schema(self):
        try:
            exec_req = ExecutionRequest.objects.create(
                user=self.user,
                func_name="test",
                input_params={
                    "geom": "Geometry",
                    "title": "Geometry",
                    "attributes": {
                        "field_str": {"type": "string"},
                        "field_int": {"type": "integer"},
                    },
                    "is_empty": True,
                },
            )

            expected_schema = [
                {"name": "field_int", "class_name": "django.db.models.IntegerField", "null": False},
                {"name": "field_str", "class_name": "django.db.models.CharField", "null": False},
                {"name": "geom", "class_name": None, "dim": 2, "authority": "EPSG:4326"},
                {"name": "fid", "class_name": "django.db.models.BigAutoField", "null": False, "primary_key": True},
            ]
            output_schema = self.handler._define_dynamic_layer_schema(None, execution_id=str(exec_req.exec_id))
            self.assertEqual(expected_schema, output_schema)

        finally:
            if exec_req:
                exec_req.delete()

    def test_publish_resources(self):
        """
        Should publish the resource via the GeoServer catalog.
        If we add the attributes, the call will also create the layer
        so we dont have to call the super()
        """
        try:
            exec_req = ExecutionRequest.objects.create(
                user=self.user,
                func_name="test",
                input_params={
                    "geom": "Geometry",
                    "title": "Geometry",
                    "attributes": {
                        "field_str": {"type": "string"},
                        "field_int": {"type": "integer"},
                    },
                    "is_empty": True,
                },
            )
            foo = FakeObj()
            catalog = MagicMock()
            catalog.http_request.return_value = foo
            resources = [{"name": "my_empty_dataset", "crs": "EPSG:4326", "exec_id": str(exec_req.exec_id)}]
            self.assertTrue(self.handler.publish_resources(resources, catalog, foo, foo))
        finally:
            if exec_req:
                exec_req.delete()

    def test_publish_resources_raise_exp_from_geoserver(self):
        """
        Should publish the resource via the GeoServer catalog.
        If we add the attributes, the call will also create the layer
        so we dont have to call the super()
        """
        try:
            exec_req = ExecutionRequest.objects.create(
                user=self.user,
                func_name="test",
                input_params={
                    "geom": "Geometry",
                    "title": "Geometry",
                    "attributes": {
                        "field_str": {"type": "string"},
                        "field_int": {"type": "integer"},
                    },
                    "is_empty": True,
                },
            )
            foo = namedtuple("FakeObj", field_names=["name", "status_code"])
            foo.name = "GeoNode"
            foo.status_code = 500
            catalog = MagicMock()
            catalog.http_request.return_value = foo
            resources = [{"name": "my_empty_dataset", "crs": "EPSG:4326", "exec_id": str(exec_req.exec_id)}]
            with self.assertRaises(Exception):
                self.handler.publish_resources(resources, catalog, foo, foo)
        finally:
            if exec_req:
                exec_req.delete()

    def test_utils_validate_attributes(self):
        """
        attributes should be valid
        """
        self.assertTrue(validate_attributes(self.attributes))

        broken_attributes = {"field_float": {"fakeey": "float"}}
        with self.assertRaises(Exception) as k:
            validate_attributes(broken_attributes)

        self.assertEqual(str(k.exception), "None is not a valid type for attribute field_float")

    def test_utils_add_attributes_to_xml(self):
        """
        attributes should be valid
        """
        subset_attributes = {"field_str": {"type": "string"}, "field_int": {"type": "integer"}}
        expected = b"<featureType><name>myname</name><nativeName>myname</nativeName><title>myname</title><srs>EPSG:4326</srs><nativeBoundingBox><minx>-180</minx><maxx>180</maxx><miny>-90</miny><maxy>90</maxy><crs>EPSG:4326</crs></nativeBoundingBox><latLonBoundingBox><minx>-180</minx><maxx>180</maxx><miny>-90</miny><maxy>90</maxy><crs>EPSG:4326</crs></latLonBoundingBox><attributes><attribute><name>field_str</name><binding>java.lang.String</binding><nillable>false</nillable></attribute><attribute><name>field_int</name><binding>java.lang.Integer</binding><nillable>false</nillable></attribute></attributes></featureType>"  # noqa
        actual_xml = add_attributes_to_xml(subset_attributes, base_xml.format(name="myname"))
        self.assertEqual(expected, actual_xml)
