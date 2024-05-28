#########################################################################
#
# Copyright (C) 2019 OSGeo
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
import os
import base64
import shutil
from django.test import override_settings
import gisdata
import requests

from django.conf import settings
from django.contrib.auth import get_user_model

from geonode import geoserver
from geonode.base import enumerations
from geonode.layers.models import Dataset
from geonode.layers.utils import get_files
from geonode.decorators import on_ogc_backend
from geonode.geoserver.helpers import gs_catalog
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.geoserver.manager import GeoServerResourceManager
from geonode.base.populate_test_data import create_single_dataset


class TestGeoServerResourceManager(GeoNodeBaseTestSupport):
    def setUp(self):
        self.files = os.path.join(gisdata.GOOD_DATA, "vector/san_andres_y_providencia_water.shp")
        self.files_as_dict, self.tmpdir = get_files(self.files)
        self.cat = gs_catalog
        self.user = get_user_model().objects.get(username="admin")
        self.sut = create_single_dataset("san_andres_y_providencia_water.shp")
        self.sut.name = "san_andres_y_providencia_water"
        self.sut.save()
        self.geoserver_url = settings.GEOSERVER_LOCATION
        self.geoserver_manager = GeoServerResourceManager()

    def tearDown(self) -> None:
        if self.tmpdir:
            shutil.rmtree(self.tmpdir, ignore_errors=True)
        return super().tearDown()

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @override_settings(ASYNC_SIGNALS=False, FILE_UPLOAD_DIRECTORY_PERMISSIONS=0o777, FILE_UPLOAD_PERMISSIONS=0o7777)
    def test_revise_resource_value_in_append_should_add_expected_rows_in_the_catalog(self):
        layer = Dataset.objects.get(name=self.sut.name)
        gs_layer = self.cat.get_layer("san_andres_y_providencia_water")
        if gs_layer is None:
            _gs_import_session_info = self.geoserver_manager._execute_resource_import(
                layer, list(self.files_as_dict.values()), self.user, action_type="create"
            )
        _gs_import_session_info = self.geoserver_manager._execute_resource_import(
            layer, list(self.files_as_dict.values()), self.user, action_type="append"
        )
        basic_auth = base64.b64encode(b"admin:geoserver")
        result = requests.get(
            f"{self.geoserver_url}/rest/imports/{_gs_import_session_info.import_session.id}",
            headers={"Authorization": f"Basic {basic_auth.decode('utf-8')}"},
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json().get("import").get("state"), enumerations.STATE_COMPLETE)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_revise_resource_value_in_replace_should_add_expected_rows_in_the_catalog(self):
        layer = Dataset.objects.get(name=self.sut.name)
        _gs_import_session_info = self.geoserver_manager._execute_resource_import(
            layer, list(self.files_as_dict.values()), self.user, action_type="replace"
        )
        basic_auth = base64.b64encode(b"admin:geoserver")
        result = requests.get(
            f"{self.geoserver_url}/rest/imports/{_gs_import_session_info.import_session.id}",
            headers={"Authorization": f"Basic {basic_auth.decode('utf-8')}"},
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json().get("import").get("state"), enumerations.STATE_COMPLETE)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_revise_resource_value_in_replace_should_return_none_for_not_existing_dataset(self):
        layer = create_single_dataset("fake_dataset")
        _gs_import_session_info = self.geoserver_manager._execute_resource_import(
            layer, list(self.files_as_dict.values()), self.user, action_type="replace"
        )
        self.assertEqual(_gs_import_session_info.import_session.state, enumerations.STATE_COMPLETE)
