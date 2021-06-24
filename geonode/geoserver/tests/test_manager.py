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
from geonode.tests.base import GeoNodeBaseTestSupport
from django.contrib.auth import get_user_model
from geonode.geoserver.manager import GeoServerResourceManager
from geonode.decorators import on_ogc_backend
from geonode.base.populate_test_data import create_single_layer
from geonode.layers.models import Layer
from geonode.geoserver.helpers import gs_catalog
from geonode.geoserver.upload import geoserver_upload
from geonode.layers.utils import get_files
from django.conf import settings
from geonode import geoserver
import requests
import gisdata
import os


class TestGeoServerResourceManager(GeoNodeBaseTestSupport):
    def setUp(self):
        self.files = os.path.join(gisdata.GOOD_DATA, "vector/san_andres_y_providencia_water.shp")
        self.files_as_dict = get_files(self.files)
        self.cat = gs_catalog
        self.user = get_user_model().objects.get(username="admin")
        self.sut = create_single_layer("san_andres_y_providencia_water")
        self.geoserver_out = geoserver_upload(
            self.sut,
            self.files,
            self.user,
            'san_andres_y_providencia_water',
            overwrite=True
        )
        self.geoserver_url = settings.GEOSERVER_LOCATION
        self.geoserver_manager = GeoServerResourceManager()

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_revise_resource_value_in_append_should_add_expected_rows_in_the_catalog(self):
        layer = Layer.objects.get(name=self.sut.name)
        _, import_session = self.geoserver_manager.revise_resource_value(layer, list(self.files_as_dict.values()), self.user, action_type="append")
        result = requests.get(f'{self.geoserver_url}/rest/imports/{import_session.id}')
        self.assertEqual(result.status_code, 200)
        actual = result.json().get('import').get('state')
        self.assertEqual('COMPLETE', actual)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_revise_resource_value_in_replace_should_add_expected_rows_in_the_catalog(self):
        layer = Layer.objects.get(name=self.sut.name)
        _, import_session = self.geoserver_manager.revise_resource_value(layer, list(self.files_as_dict.values()), self.user, action_type="replace")
        result = requests.get(f'{self.geoserver_url}/rest/imports/{import_session.id}')
        self.assertEqual(result.status_code, 200)
        actual = result.json().get('import').get('state')
        self.assertEqual('COMPLETE', actual)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_revise_resource_value_in_replace_should_return_none_for_not_existing_layer(self):
        layer = create_single_layer('fake_layer')
        with self.assertRaises(Exception):
            self.geoserver_manager.revise_resource_value(layer, list(self.files_as_dict.values()), self.user, action_type="replace")
