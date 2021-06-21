#########################################################################
#
# Copyright (C) 2017 OSGeo
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

import os
import dj_database_url

from django.conf import settings
from django.urls import reverse

from geonode import geoserver
from geonode import GeoNodeException
from geonode.layers.models import Layer
from geonode.decorators import on_ogc_backend
from geonode.geoserver.signals import gs_catalog

from .utils import create_layer


r"""
How to run the tests
--------------------

Create a user and database for the datastore:

    $ sudo su postgres
    $ psql
    postgres=# CREATE USER geonode with password 'geonode';
    postgres=# ALTER USER geonode WITH LOGIN;
    postgres=# ALTER USER geonode WITH SUPERUSER;
    postgres=# CREATE DATABASE datastore WITH OWNER geonode;
    postgres=# \c datastore
    datastore=# CREATE EXTENSION postgis;

Add 'geonode.geoserver.createlayer' in GEONODE_INTERNAL_APPS

Then, as usual, run "paver run_tests"

"""


class CreateLayerCoreTest(GeoNodeBaseTestSupport):

    """
    Test createlayer application.
    """
    fixtures = ['initial_data.json', 'bobby']

    def setUp(self):
        super().setUp()
        # createlayer must use postgis as a datastore
        # set temporary settings to use a postgis datastore
        DATASTORE_URL = 'postgis://geonode:geonode@localhost:5432/datastore'
        postgis_db = dj_database_url.parse(DATASTORE_URL, conn_max_age=0)
        settings.DATABASES['datastore'] = postgis_db
        settings.OGC_SERVER['default']['DATASTORE'] = 'datastore'

    def tearDown(self):
        super(GeoNodeBaseTestSupport, self).tearDown()
        # move to original settings
        settings.OGC_SERVER['default']['DATASTORE'] = ''
        del settings.DATABASES['datastore']
        # TODO remove stuff from django and geoserver catalog

    def test_layer_creation_without_postgis(self):
        # TODO implement this: must raise an error message
        pass

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_layer_creation(self):
        """
        Try creating a layer.
        """
        internal_apps_tests = os.environ.get('TEST_RUN_INTERNAL_APPS', None)
        if not internal_apps_tests:
            internal_apps_tests = settings.internal_apps_tests
        else:
            layer_name = 'point_layer'
            layer_title = 'A layer for points'

            create_layer(
                layer_name,
                layer_title,
                'bobby',
                'Point'
            )

            cat = gs_catalog

            # Check the layer is in the Django database
            layer = Layer.objects.get(name=layer_name)

            # check if it is in geoserver
            gs_layer = cat.get_layer(layer_name)
            self.assertIsNotNone(gs_layer)
            self.assertEqual(gs_layer.name, layer_name)

            resource = gs_layer.resource
            # we must have only one attibute ('the_geom')
            self.assertEqual(len(resource.attributes), 1)

            # check layer corrispondence between django and geoserver
            self.assertEqual(resource.title, layer_title)
            self.assertEqual(resource.projection, layer.srid)

            # check if layer detail page is accessible with client
            response = self.client.get(reverse('layer_detail', args=(f'geonode:{layer_name}',)))
            self.assertEqual(response.status_code, 200)

    def test_layer_creation_with_wrong_geometry_type(self):
        """
        Try creating a layer with uncorrect geometry type.
        """
        with self.assertRaises(GeoNodeException):
            create_layer(
                'wrong_geom_layer',
                'A layer with wrong geometry',
                'bobby',
                'wrong_geometry')

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_layer_creation_with_attributes(self):
        """
        Try creating a layer with attributes.
        """
        internal_apps_tests = os.environ.get('TEST_RUN_INTERNAL_APPS', None)
        if not internal_apps_tests:
            internal_apps_tests = settings.internal_apps_tests

        else:
            attributes = """
            {
              "field_str": "string",
              "field_int": "integer",
              "field_date": "date",
              "field_float": "float"
            }
            """

            layer_name = 'attributes_layer'
            layer_title = 'A layer with attributes'

            create_layer(
                layer_name,
                layer_title,
                'bobby',
                'Point',
                attributes
            )

            cat = gs_catalog
            gs_layer = cat.get_layer(layer_name)
            resource = gs_layer.resource

            # we must have one attibute for the geometry, and 4 other ones
            self.assertEqual(len(resource.attributes), 5)

    def test_layer_creation_with_permissions(self):
        """
        Try creating a layer with permissions.
        """
        # TODO
        pass
