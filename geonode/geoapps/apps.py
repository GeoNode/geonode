#########################################################################
#
# Copyright (C) 2020 OSGeo
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
from django.apps import AppConfig
from django.utils.translation import gettext_noop as _
from geonode.notifications_helper import NotificationsAppConfigBase


class GeoNodeAppsConfig(NotificationsAppConfigBase, AppConfig):
    name = "geonode.geoapps"
    type = "GEONODE_APP"

    NOTIFICATIONS = (
        (
            "geoapp_created",
            _("App Created"),
            _("A App was created"),
        ),
        (
            "geoapp_updated",
            _("App Updated"),
            _("A App was updated"),
        ),
        (
            "geoapp_approved",
            _("App Approved"),
            _("A App was approved by a Manager"),
        ),
        (
            "geoapp_published",
            _("App Published"),
            _("A App was published"),
        ),
        (
            "geoapp_deleted",
            _("App Deleted"),
            _("A App was deleted"),
        ),
        (
            "geoapp_rated",
            _("Rating for App"),
            _("A rating was given to an App"),
        ),
    )
