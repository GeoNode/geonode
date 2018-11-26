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



class EditDataCoreTest(GeoNodeBaseTestSupport):


    def test_add_row(self):

        layer_name = 'test_1'
        feature_type = 'Point'

        data_dict = {"data":"OID_=,Name=carribean6,Status=,ADM1_NAME=","feature_type":"Point","layer_name":"test_1","coords":[-69.06250000000001, 8.407168163601076]}

        save_added_row(layer_name, feature_type, data_dict)
    '''
    def test_edits(self):

        layer_name = 'test_1'
        feature_id = 24

        data_dict = {"data":"Name=I am a test,Status=Modified3","feature_id":feature_id,"layer_name":layer_name}
        save_edits(layer_name, feature_id, data_dict)

    def test_geom_edits(self):

        layer_name = 'test_1'
        feature_id = 'test_1.22'

        coords = '23.5624423119 -83.6654376984'
        save_geom_edits(layer_name, feature_id, coords)


    def test_delete(self):

        layer_name = 'test_1'
        feature_id = 'test_1.23'

        delete_selected_row(layer_name, feature_id)
    '''
