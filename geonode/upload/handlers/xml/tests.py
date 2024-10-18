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
import shutil
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from geonode.base.populate_test_data import create_single_dataset
from geonode.upload import project_dir
from geonode.upload.models import ResourceHandlerInfo
from geonode.upload.orchestrator import orchestrator
from geonode.upload.handlers.xml.exceptions import InvalidXmlException
from geonode.upload.handlers.xml.handler import XMLFileHandler


class TestXMLFileHandler(TestCase):
    databases = ("default", "datastore")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = XMLFileHandler()
        cls.valid_xml = f"{settings.PROJECT_ROOT}/base/fixtures/test_xml.xml"
        cls.invalid_xml = f"{project_dir}/tests/fixture/invalid.gpkg"

        shutil.copy(cls.valid_xml, "/tmp")
        cls.user, _ = get_user_model().objects.get_or_create(username="admin")
        cls.invalid_files = {"base_file": cls.invalid_xml, "xml_file": cls.invalid_xml}
        cls.valid_files = {
            "base_file": "/tmp/test_xml.xml",
            "xml_file": "/tmp/test_xml.xml",
            "action": "resource_metadata_upload",
        }
        cls.owner = get_user_model().objects.first()
        cls.layer = create_single_dataset(name="extruded_polygon", owner=cls.owner)

    def setUp(self) -> None:
        shutil.copy(self.valid_xml, "/tmp")
        super().setUp()

    def test_task_list_is_the_expected_one(self):
        expected = (
            "start_import",
            "geonode.upload.import_resource",
        )
        self.assertEqual(len(self.handler.TASKS["resource_metadata_upload"]), 2)
        self.assertTupleEqual(expected, self.handler.TASKS["resource_metadata_upload"])

    def test_is_valid_should_raise_exception_if_the_xml_is_invalid(self):
        with self.assertRaises(InvalidXmlException) as _exc:
            self.handler.is_valid(files=self.invalid_files)

        self.assertIsNotNone(_exc)
        self.assertTrue("Uploaded document is not XML or is invalid" in str(_exc.exception.detail))

    def test_is_valid_should_pass_with_valid_xml(self):
        self.handler.is_valid(files=self.valid_files)

    def test_can_handle_should_return_true_for_xml(self):
        actual = self.handler.can_handle(self.valid_files)
        self.assertTrue(actual)

    def test_can_handle_should_return_false_for_other_files(self):
        actual = self.handler.can_handle({"base_file": "random.file"})
        self.assertFalse(actual)

    @override_settings(MEDIA_ROOT="/tmp/")
    def test_can_successfully_import_metadata_file(self):
        exec_id = orchestrator.create_execution_request(
            user=get_user_model().objects.first(),
            func_name="funct1",
            step="step",
            input_params={
                "files": self.valid_files,
                "resource_pk": self.layer.pk,
                "skip_existing_layer": True,
                "handler_module_path": str(self.handler),
            },
        )
        ResourceHandlerInfo.objects.create(
            resource=self.layer,
            handler_module_path="geonode.upload.handlers.shapefile.handler.ShapeFileHandler",
        )

        self.assertEqual(self.layer.title, "extruded_polygon")

        self.handler.import_resource({}, str(exec_id))

        self.layer.refresh_from_db()
        self.assertEqual(self.layer.title, "test_dataset")
