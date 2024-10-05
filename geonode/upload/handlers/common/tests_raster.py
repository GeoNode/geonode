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
from django.test import TestCase
from mock import patch
from geonode.upload.handlers.common.raster import BaseRasterFileHandler
from django.contrib.auth import get_user_model
from geonode.upload import project_dir
from geonode.upload.orchestrator import orchestrator
from geonode.base.populate_test_data import create_single_dataset
from geonode.resource.models import ExecutionRequest


class TestBaseRasterFileHandler(TestCase):
    databases = ("default",)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = BaseRasterFileHandler()
        cls.valid_raster = f"{project_dir}/tests/fixture/test_raster.tif"
        cls.user, _ = get_user_model().objects.get_or_create(username="admin")
        cls.valid_files = {"base_file": cls.valid_raster}
        cls.owner = get_user_model().objects.first()
        cls.layer = create_single_dataset(name="test_grid", owner=cls.owner)

    def test_create_error_log(self):
        """
        Should return the formatted way for the log of the handler
        """
        actual = self.handler.create_error_log(
            Exception("my exception"),
            "foo_task_name",
            *["exec_id", "layer_name", "alternate"],
        )
        expected = "Task: foo_task_name raised an error during actions for layer: alternate: my exception"
        self.assertEqual(expected, actual)

    @patch("geonode.upload.handlers.common.vector.BaseVectorFileHandler.get_ogr2ogr_driver")
    @patch("geonode.upload.handlers.common.vector.chord")
    def test_import_resource_should_not_be_imported(self, celery_chord, ogr2ogr_driver):
        """
        If the resource exists and should be skept, the celery task
        is not going to be called and the layer is skipped
        """
        exec_id = None
        try:
            # create the executionId
            exec_id = orchestrator.create_execution_request(
                user=get_user_model().objects.first(),
                func_name="funct1",
                step="step",
                input_params={"files": self.valid_files, "skip_existing_layer": True},
            )

            # start the resource import
            self.handler.import_resource(files=self.valid_files, execution_id=str(exec_id))

            celery_chord.assert_not_called()
        finally:
            if exec_id:
                ExecutionRequest.objects.filter(exec_id=exec_id).delete()

    @patch("geonode.upload.handlers.common.raster.import_orchestrator.apply_async")
    def test_import_resource_should_work(self, import_orchestrator):
        try:
            exec_id = orchestrator.create_execution_request(
                user=get_user_model().objects.first(),
                func_name="funct1",
                step="step",
                input_params={"files": self.valid_files},
            )

            # start the resource import
            self.handler.import_resource(files=self.valid_files, execution_id=str(exec_id))

            import_orchestrator.assert_called_once()
        finally:
            if exec_id:
                ExecutionRequest.objects.filter(exec_id=exec_id).delete()
