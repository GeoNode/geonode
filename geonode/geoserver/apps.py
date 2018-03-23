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

    def ready(self):
        """Connect relevant signals to their corresponding handlers"""
        # use different name to avoid module clash
        from . import BACKEND_PACKAGE
        from geonode.utils import check_ogc_backend

        if check_ogc_backend(BACKEND_PACKAGE):
            from .signals import (geoserver_pre_delete,  # noqa
                                  geoserver_pre_save,  # noqa
                                  geoserver_post_save,  # noqa
                                  geoserver_post_save_local,  # noqa
                                  geoserver_pre_save_maplayer,  # noqa
                                  geoserver_post_save_map)  # noqa

        super(GeoserverAppConfig, self).ready()
