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


class LayersAppConfig(NotificationsAppConfigBase):
    name = 'geonode.layers'
    NOTIFICATIONS = (
        ("layer_created", _("Dataset Created"), _("A Dataset was created"),),
        ("layer_updated", _("Dataset Updated"), _("A Dataset was updated"),),
        ("layer_approved", _("Dataset Approved"), _("A Dataset was approved by a Manager"),),
        ("layer_published", _("Dataset Published"), _("A Dataset was published"),),
        ("layer_deleted", _("Dataset Deleted"), _("A Dataset was deleted"),),
        ("layer_comment", _("Comment on Dataset"), _("A layer was commented on"),),
        ("layer_rated", _("Rating for Dataset"), _("A rating was given to a layer"),),)


default_app_config = 'geonode.layers.LayersAppConfig'
