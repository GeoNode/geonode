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
from unittest.mock import patch
from geonode.tasks.tasks import send_queued_notifications


class TasksTest(GeoNodeBaseTestSupport):
    @patch("geonode.notifications_helper.has_notifications", False)
    def test_send_queued_notifications_is_not_called_if_notification_is_off(self):
        actual = send_queued_notifications()
        self.assertIsNone(actual)
