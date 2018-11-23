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
        feature_id = 16
        feature_type = 'Point'

        data = ['Name=I am a test','Status=I am a test']
        data_dict = {'coords': [-4.570312500000001, 40.44694705960048], 'data': 'Name=I am a test,Status=I am a test', 'feature_type': feature_type, 'layer_name': layer_name}
        save_added_row(layer_name, feature_type, data, data_dict)

    def test_edits(self):

        layer_name = 'test_1'
        feature_id = 16
        feature_type = 'Point'

        data_dict = {"data":"Name=I am a test,Status=Modified","feature_id":feature_id,"layer_name":layer_name}
        save_edits(layer_name, feature_type, data_dict)

    def geom_edits(self):

        layer_name = 'test_1'
        feature_id = 16
        feature_type = 'Point'

        coords = [12.612991333007812,41.73237975329554]
        save_geom_edits(layer_name, feature_id, coords)

    def test_delete(self):

        layer_name = 'test_1'
        feature_id = 16
        feature_type = 'Point'

        delete_selected_row(layer_name, feature_id)
