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

import dj_database_url

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from guardian.shortcuts import get_anonymous_user

from geonode.geoserver.signals import gs_catalog
from geonode import GeoNodeException
from geonode.layers.models import Layer

from geonode.contrib.edit_data.utils import *
from geonode.contrib.edit_data import *

from geonode.contrib.createlayer.utils import create_layer

"""
How to run the tests
--------------------

These tests use the functionality of the createlayer contrib app in order to
create a test layer.

Create a user and database for the datastore:

    $ sudo su postgres
    $ psql
    postgres=# CREATE USER geonode with password 'geonode';
    postgres=# ALTER USER geonode WITH LOGIN;
    postgres=# ALTER USER geonode WITH SUPERUSER;
    postgres=# CREATE DATABASE datastore WITH OWNER geonode;
    postgres=# \c datastore
    datastore=# CREATE EXTENSION postgis;

Add 'geonode.contrib.createlayer' in GEONODE_CONTRIB_APPS

Then, as usual, run "paver run_tests"

"""

class EditDataCoreTest(GeoNodeBaseTestSupport):

    layer_name = 'test_layer'
    feature_id = 1
    layer_feature_id = '.'.join([layer_name,str(feature_id)])

    '''
    # taken from Paolo's createlayer contrib app
    def setUp(self):
        super(EditDataCoreTest, self).setUp()
        # createlayer must use postgis as a datastore
        # set temporary settings to use a postgis datastore
        DATASTORE_URL = 'postgis://geonode:geonode@localhost:5432/datastore'
        postgis_db = dj_database_url.parse(DATASTORE_URL, conn_max_age=600)
        settings.DATABASES['datastore'] = postgis_db
        settings.OGC_SERVER['default']['DATASTORE'] = 'datastore'

    def tearDown(self):
        super(GeoNodeBaseTestSupport, self).tearDown()
        # move to original settings
        settings.OGC_SERVER['default']['DATASTORE'] = ''
        del settings.DATABASES['datastore']
        # TODO remove stuff from django and geoserver catalog

    # taken from Paolo's createlayer contrib app
    def test_layer_creation(self):
        """
        Try creating a layer.
        """

        layer_title = 'A layer for points'

        create_layer(
            self.layer_name,
            layer_title,
            'bobby',
            'Point'
        )

        cat = gs_catalog

        # Check the layer is in the Django database
        layer = Layer.objects.get(name=self.layer_name)

        # check if it is in geoserver
        gs_layer = cat.get_layer(self.layer_name)
        self.assertIsNotNone(gs_layer)
        self.assertEqual(gs_layer.name, self.layer_name)

        resource = gs_layer.resource
        # we must have only one attibute ('the_geom')
        self.assertEqual(len(resource.attributes), 1)

        # check layer corrispondence between django and geoserver
        self.assertEqual(resource.title, layer_title)
        self.assertEqual(resource.projection, layer.srid)

        # check if layer detail page is accessible with client
        response = self.client.get(reverse('layer_detail', args=('geonode:%s' % self.layer_name,)))
        self.assertEqual(response.status_code, 200)

    '''

    def test_add_row(self):

        #layer_name = self.layer_name
        feature_type = 'Point'

        data_dict = {"data":"FID_1=,Name__EN_=papagou,Name__FR_=,Address__E=,Address__A=,Longitude=,Latitude=,Region__EN=,ATM_IDs=,FID_2=,FID_1_1=,objectid=,admin0name=,admin0na_1=,admin0pcod=,admin1name=,admin1na_1=,admin1pcod=,admin2name=,admin2na_1=,admin2pcod=,admin2refn=,admin2altn=,admin2al_1=,admin2al_2=,admin2al_3=,lastupdate=,validon=,validto=,st_area_sh=,st_length_=,Modality=,Count_=","feature_type":"Point","layer_name":self.layer_name,"coords":[22.930927,40.640600]}


        success, message, status_code = save_added_row(self.layer_name, feature_type, data_dict)
        self.assertEqual(status_code, 200)


    def test_edits(self):

        data_dict = {"data":"FID_1=,Name__EN_=ioannina,Name__FR_=13,Address__E=,Address__A=,Longitude=,Latitude=,Region__EN=,ATM_IDs=,FID_2=,FID_1_1=,objectid=,admin0name=,admin0na_1=,admin0pcod=,admin1name=,admin1na_1=,admin1pcod=,admin2name=,admin2na_1=,admin2pcod=,admin2refn=,admin2altn=,admin2al_1=,admin2al_2=,admin2al_3=,lastupdate=,validon=,validto=,st_area_sh=,st_length_=,Modality=,Count_=","feature_id":self.feature_id,"layer_name":self.layer_name}

        success, message, status_code = save_edits(self.layer_name, self.feature_id, data_dict)
        self.assertEqual(status_code, 200)


    def test_geom_edits(self):

        coords = '39.629287 20.886753'
        success, message, status_code = save_geom_edits(self.layer_name, self.layer_feature_id, coords)
        self.assertEqual(status_code, 200)

    def test_delete(self):

        success, message, status_code = delete_selected_row(self.layer_name, self.layer_feature_id)
        self.assertEqual(status_code, 200)
