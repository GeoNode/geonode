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
import logging
import faulthandler

from django.test.testcases import (
    TestCase,
    SimpleTestCase,
    LiveServerTestCase)

try:
    from django.utils.decorators import classproperty
except Exception:
    class classproperty:

        def __init__(self, method=None):
            self.fget = method

        def __get__(self, instance, cls=None):
            return self.fget(cls)

        def getter(self, method):
            self.fget = method
            return self

logger = logging.getLogger(__name__)


class GeoNodeBaseSimpleTestSupport(SimpleTestCase):
    pass


class GeoNodeBaseTestSupport(TestCase):

    type = None
    obj_ids = []
    integration = False

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

    @classproperty
    def get_obj_ids(cls):
        return cls.obj_ids

    @classproperty
    def get_integration(cls):
        return cls.integration

    @classproperty
    def get_type(cls):
        return cls.type

    def setUp(self):
        super().setUp()
        faulthandler.enable()


class GeoNodeLiveTestSupport(GeoNodeBaseTestSupport,
                             LiveServerTestCase):

    integration = True
    port = 8000
