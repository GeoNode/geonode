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

from django.utils.translation import ugettext_noop as _
from geonode.notifications_helper import NotificationsAppConfigBase


class GeoserverAppConfig(NotificationsAppConfigBase):
    name = 'geonode.geoserver'
    NOTIFICATIONS = (("layer_uploaded", _("Layer Uploaded"), _("A layer was uploaded"),),
                     ("layer_comment", _("Comment on Layer"), _("A layer was commented on"),),
                     ("layer_rated", _("Rating for Layer"), _("A rating was given to a layer"),),
                     )


default_app_config = 'geonode.geoserver.GeoserverAppConfig'

BACKEND_PACKAGE = 'geonode.geoserver'
