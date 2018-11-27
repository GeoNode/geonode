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

    '''
    def test_add_row(self):

        layer_name = 'atms_dist_1'
        feature_type = 'Point'

        data_dict = {"data":"FID_1=,Name__EN_=thessaloniki,Name__FR_=,Address__E=,Address__A=,Longitude=,Latitude=,Region__EN=,ATM_IDs=,FID_2=,FID_1_1=,objectid=,admin0name=,admin0na_1=,admin0pcod=,admin1name=,admin1na_1=,admin1pcod=,admin2name=,admin2na_1=,admin2pcod=,admin2refn=,admin2altn=,admin2al_1=,admin2al_2=,admin2al_3=,lastupdate=,validon=,validto=,st_area_sh=,st_length_=,Modality=,Count_=","feature_type":"Point","layer_name":"atms_dist_1","coords":[22.930927,40.640600]}


        save_added_row(layer_name, feature_type, data_dict)

    def test_edits(self):

        layer_name = 'atms_dist_1'
        feature_id = 118

        data_dict = {"data":"FID_1=,Name__EN_=ioannina,Name__FR_=12,Address__E=,Address__A=,Longitude=,Latitude=,Region__EN=,ATM_IDs=,FID_2=,FID_1_1=,objectid=,admin0name=,admin0na_1=,admin0pcod=,admin1name=,admin1na_1=,admin1pcod=,admin2name=,admin2na_1=,admin2pcod=,admin2refn=,admin2altn=,admin2al_1=,admin2al_2=,admin2al_3=,lastupdate=,validon=,validto=,st_area_sh=,st_length_=,Modality=,Count_=","feature_id":feature_id,"layer_name":layer_name}
        save_edits(layer_name, feature_id, data_dict)

    def test_geom_edits(self):

        layer_name = 'atms_dist_1'
        feature_id = 'atms_dist_1.118'

        coords = '39.629287 20.886753'
        save_geom_edits(layer_name, feature_id, coords)

    '''
    def test_delete(self):

        layer_name = 'atms_dist_1'
        feature_id = 'atms_dist_1.118'

        delete_selected_row(layer_name, feature_id)
