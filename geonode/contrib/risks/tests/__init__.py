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

import os

from django.test import TestCase
from django.db import connections
from django.core.management import call_command

from geonode.utils import designals, resignals

TESTDATA_SQL_INIT = os.path.join(
    os.path.dirname(__file__),
    'resources/test_data_setup.sql')

TESTDATA_SQL_TEARDOWN = os.path.join(
    os.path.dirname(__file__),
    'resources/test_data_teardown.sql')

class RisksTestCase(TestCase):
    fixtures = [
        'sample_admin',
        'default_oauth_apps',
        'initial_data',
        '001_risks_adm_divisions',
        '002_risks_hazards',
        '003_risks_analysis',
        '004_risks_dymension_infos',
        '005_risks_test_base'
    ]

    def setUp(self):
        # Test initialization
        designals()
        call_command('loaddata', '005_risks_test_layer')

        # Prepare Test Tables
        with connections['datastore'].cursor() as cursor:
            sql_file = open(TESTDATA_SQL_INIT, 'r')
            sql = " ".join(sql_file.readlines())
            cursor.execute(sql)
            connections['datastore'].commit()
            sql_file.close()

    def tearDown(self):
        # Test deinit
        resignals()

        # Cleanup Test Tables
        with connections['datastore'].cursor() as cursor:
            sql_file = open(TESTDATA_SQL_TEARDOWN, 'r')
            sql = " ".join(sql_file.readlines())
            cursor.execute(sql)
            connections['datastore'].commit()
            sql_file.close()
