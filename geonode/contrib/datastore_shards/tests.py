# -*- coding: utf-8 -*-
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
import datetime
import dj_database_url
import gisdata
import mock
import logging

from django.conf import settings
from django.contrib.auth import get_user_model

from geonode.geoserver.signals import gs_catalog
from geonode.layers.models import Layer
from geonode.layers.utils import file_upload

from .models import Database

logger = logging.getLogger(__name__)

"""
How to run the tests
--------------------

Add 'geonode.contrib.datastore_shards' in GEONODE_CONTRIB_APPS, and then
add the following settings:

# SHARD DATABASES SETTINGS
# SHARD_STRATEGY may be yearly, monthly, layercount
SHARD_STRATEGY = 'monthly'
SHARD_LAYER_COUNT = 100
SHARD_PREFIX = 'wm_'
SHARD_SUFFIX = ''

Make sure the postgis user (geonode in this test code) has createdb privilege
in PostgreSQL.

Then, as usual, run "paver run_tests"

"""

SHARD_LAYER_COUNT = 2
SHARD_PREFIX = 'testshards_'

YEAR = 1971
MONTH = 2


def mocked_get_today():
    """
    Mock for get_today used by yearly and monthly shards.
    """
    return datetime.date(YEAR, MONTH, 1)


class DatastoreShardsCoreTest(GeoNodeBaseTestSupport):
    """
    Test the datastore_shards application.
    """

    def setUp(self):
        super(DatastoreShardsCoreTest, self).setUp()
        # set temporary settings to use a postgis datastore
        settings.DATASTORE_URL = 'postgis://geonode:geonode@localhost:5432/datastore'
        postgis_db = dj_database_url.parse(settings.DATASTORE_URL, conn_max_age=600)
        settings.DATABASES['datastore'] = postgis_db
        settings.OGC_SERVER['default']['DATASTORE'] = 'datastore'
        settings.SHARD_STRATEGY = 'layercount'
        settings.SHARD_LAYER_COUNT = SHARD_LAYER_COUNT
        settings.SHARD_PREFIX = SHARD_PREFIX

    def tearDown(self):
        super(GeoNodeBaseTestSupport, self).tearDown()
        # move to original settings
        settings.OGC_SERVER['default']['DATASTORE'] = ''
        del settings.DATABASES['datastore']

    def test_layercount_strategy(self):
        """
        Test layercount SHARD_STRATEGY.
        """
        settings.SHARD_STRATEGY = 'layercount'

        owner = get_user_model().objects.get(username="bobby")
        layers_to_upload = ('layer_01', 'layer_02', 'layer_03', 'layer_04', 'layer_05')
        for layer in layers_to_upload:
            logger.debug('Uploading layer %s...' % layer)
            saved_layer = file_upload(
                os.path.join(gisdata.VECTOR_DATA, 'san_andres_y_providencia_poi.shp'),
                name=layer,
                user=owner,
                overwrite=True,
            )
            saved_layer.set_default_permissions()

        # check layers in geoserver if they have correct store type and datasource
        cat = gs_catalog
        i = 0
        for layer in layers_to_upload:
            i += 1
            gs_layer = cat.get_layer(layer)
            self.assertEqual(gs_layer.resource.store.type, 'PostGIS')
            if i in (1, 2):
                self.assertEqual(gs_layer.resource.store.name, '%s00000' % SHARD_PREFIX)
            if i in (3, 4):
                self.assertEqual(gs_layer.resource.store.name, '%s00001' % SHARD_PREFIX)
            if i == 5:
                self.assertEqual(gs_layer.resource.store.name, '%s00002' % SHARD_PREFIX)

        # remove one layer and see what happens when adding a new one
        layer = Layer.objects.get(name='layer_05')
        layer.delete()

        saved_layer = file_upload(
            os.path.join(gisdata.VECTOR_DATA, 'san_andres_y_providencia_poi.shp'),
            name='layer_06',
            user=owner,
            overwrite=True,
        )
        saved_layer.set_default_permissions()

        gs_layer = cat.get_layer('layer_06')
        self.assertEqual(gs_layer.resource.store.type, 'PostGIS')
        self.assertEqual(gs_layer.resource.store.name, '%s00002' % SHARD_PREFIX)

        # check Database objects and layers_count
        self.assertEqual(
            Database.objects.filter(name__contains=('%s0000' % SHARD_PREFIX)).count(), 3
        )
        self.assertEqual(
            Database.objects.get(name='%s00000' % SHARD_PREFIX).layers_count, 2
        )
        self.assertEqual(
            Database.objects.get(name='%s00001' % SHARD_PREFIX).layers_count, 2
        )
        self.assertEqual(
            Database.objects.get(name='%s00002' % SHARD_PREFIX).layers_count, 1
        )

        # remove layers
        layers_to_delete = ('layer_01', 'layer_02', 'layer_03', 'layer_04', 'layer_06')
        for layer_name in layers_to_delete:
            layer = Layer.objects.get(name=layer_name)
            layer.delete()

        for i in (0, 1, 2):
            self.assertEqual(
                Database.objects.get(name='%s0000%s' % (SHARD_PREFIX, i)).layers_count, 0
            )

    @mock.patch('geonode.contrib.datastore_shards.utils.get_today', side_effect=mocked_get_today)
    def test_monthly_strategy(self, mock_obj):
        """
        Test monthly SHARD_STRATEGY.
        """
        settings.SHARD_STRATEGY = 'monthly'

        # testing if layer is created in 197102 shard
        global MONTH
        MONTH = 2

        owner = get_user_model().objects.get(username="bobby")
        saved_layer = file_upload(
            os.path.join(gisdata.VECTOR_DATA, 'san_andres_y_providencia_poi.shp'),
            name='layer_a',
            user=owner,
            overwrite=True,
        )
        saved_layer.set_default_permissions()

        cat = gs_catalog
        gs_layer = cat.get_layer('layer_a')
        self.assertEqual(gs_layer.resource.store.type, 'PostGIS')
        self.assertEqual(gs_layer.resource.store.name, '%s197102' % SHARD_PREFIX)

        # afer one month
        # testing if layer is created in 197103 shard
        global MONTH
        MONTH = 3
        saved_layer = file_upload(
            os.path.join(gisdata.VECTOR_DATA, 'san_andres_y_providencia_poi.shp'),
            name='layer_b',
            user=owner,
            overwrite=True,
        )
        saved_layer.set_default_permissions()

        gs_layer = cat.get_layer('layer_b')
        self.assertEqual(gs_layer.resource.store.type, 'PostGIS')
        self.assertEqual(gs_layer.resource.store.name, '%s197103' % SHARD_PREFIX)

        # check Database objects
        self.assertEqual(
            Database.objects.filter(name__contains=('%s1971' % SHARD_PREFIX)).count(),
            2)
        self.assertEqual(
            Database.objects.get(name='%s197102' % SHARD_PREFIX).layers_count, 1
        )
        self.assertEqual(
            Database.objects.get(name='%s197103' % SHARD_PREFIX).layers_count, 1
        )

        # remove the layers and see what happens
        for layer_name in ('layer_a', 'layer_b'):
            layer = Layer.objects.get(name=layer_name)
            layer.delete()

        self.assertEqual(
            Database.objects.get(name='%s197102' % SHARD_PREFIX).layers_count, 0
        )
        self.assertEqual(
            Database.objects.get(name='%s197103' % SHARD_PREFIX).layers_count, 0
        )
