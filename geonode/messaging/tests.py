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

from geonode.messaging.apps import connection
from geonode.messaging.consumer import Consumer


class MessagingTest(GeoNodeBaseTestSupport):
    """
    Tests geonode.messaging
    """

    type = "dataset"

    def setUp(self):
        super().setUp()

        self.adm_un = "admin"
        self.adm_pw = "admin"

    def test_consumer(self):
        with connection:
            try:
                worker = Consumer(connection)
                self.assertTrue(worker is not None)
            except Exception:
                self.fail("could not create a Consumer.")
