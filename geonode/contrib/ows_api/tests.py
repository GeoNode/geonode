# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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

import json

from geonode.tests.base import GeoNodeBaseTestSupport

from geonode.base.populate_test_data import create_models
from geonode.base.models import Link


class OWSApiTestCase(GeoNodeBaseTestSupport):

    def setUp(self):
        super(OWSApiTestCase, self).setUp()
        create_models(type='layer')
        # prepare some WMS endpoints
        q = Link.objects.all()
        for l in q[:3]:
            l.link_type = 'OGC:WMS'
            l.save()

    def test_ows_api(self):
        url = '/api/ows_endpoints/'
        q = Link.objects.filter(link_type__startswith="OGC:")
        self.assertEqual(q.count(), 3)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(len(data['data']), q.count())
