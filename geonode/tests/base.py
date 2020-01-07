# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 OSGeo
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
# along with this profgram. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.test.testcases import SimpleTestCase, TestCase, LiveServerTestCase

try:
    from django.utils.decorators import classproperty
except BaseException:
    class classproperty(object):

        def __init__(self, method=None):
            self.fget = method

        def __get__(self, instance, cls=None):
            return self.fget(cls)

        def getter(self, method):
            self.fget = method
            return self

from geonode import geoserver, qgis_server  # noqa
from geonode.utils import check_ogc_backend
from geonode.base.populate_test_data import create_models, remove_models

import logging

logger = logging.getLogger(__name__)


class GeoNodeBaseSimpleTestSupport(SimpleTestCase):
    pass


class GeoNodeBaseTestSupport(TestCase):

    type = None
    obj_ids = []

    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        fixtures = [
            'initial_data.json',
            'group_test_data.json',
            'default_oauth_apps.json'
        ]
    else:
        fixtures = [
            'initial_data.json',
            'group_test_data.json'
        ]

    @classproperty
    def get_type(cls):
        return cls.type

    @classproperty
    def get_obj_ids(cls):
        return cls.obj_ids

    def setUp(self):
        super(GeoNodeBaseTestSupport, self).setUp()
        logging.info(" Test setUp. Creating models.")
        self.get_obj_ids = create_models(type=self.get_type)


class GeoNodeLiveTestSupport(GeoNodeBaseTestSupport,
                             LiveServerTestCase):

    port = 8000

    def setUp(self):
        super(GeoNodeLiveTestSupport, self).setUp()
        logging.info(" Test setUp. Creating models.")
        self.get_obj_ids = create_models(type=self.get_type)

    def tearDown(self):
        super(GeoNodeLiveTestSupport, self).tearDown()
        logging.info(" Test tearDown. Destroying models / Cleaning up Server.")
        remove_models(self.get_obj_ids, type=self.get_type)
        from django.conf import settings
        if settings.OGC_SERVER['default'].get(
                "GEOFENCE_SECURITY_ENABLED", False):
            from geonode.security.utils import purge_geofence_all
            purge_geofence_all()
