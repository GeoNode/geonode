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
from geonode.upload import project_dir
from geonode.upload.orchestrator import orchestrator
from geonode.upload.datastore import DataStoreManager
from django.contrib.auth import get_user_model


class TestDataStoreManager(TestCase):
    """ """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.files = {"base_file": f"{project_dir}/tests/fixture/valid.gpkg"}

    def setUp(self):
        self.user = get_user_model().objects.first()
        execution_id = orchestrator.create_execution_request(
            user=self.user,
            func_name="create",
            step="create",
            action="upload",
            input_params={
                **{"handler_module_path": "geonode.upload.handlers.gpkg.handler.GPKGFileHandler"},
            },
        )
        self.datastore = DataStoreManager(
            self.files, "geonode.upload.handlers.gpkg.handler.GPKGFileHandler", self.user, execution_id
        )

        execution_id_url = orchestrator.create_execution_request(
            user=self.user,
            func_name="create",
            step="create",
            action="upload",
            input_params={"url": "https://geosolutionsgroup.com"},
        )
        self.datastore_url = DataStoreManager(
            self.files, "geonode.upload.handlers.common.remote.BaseRemoteResourceHandler", self.user, execution_id_url
        )
        self.gpkg_path = f"{project_dir}/tests/fixture/valid.gpkg"

    def test_input_is_valid_with_files(self):
        self.assertTrue(self.datastore.input_is_valid())

    def test_input_is_valid_with_urls(self):
        self.assertTrue(self.datastore_url.input_is_valid())
