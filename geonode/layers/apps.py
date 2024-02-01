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

from django.apps import AppConfig
from django.utils.translation import gettext_noop as _
from geonode.notifications_helper import NotificationsAppConfigBase


class DatasetAppConfig(NotificationsAppConfigBase, AppConfig):
    name = "geonode.layers"
    verbose_name = "Dataset"
    verbose_name_plural = "Datasets"
    NOTIFICATIONS = (
        (
            "dataset_created",
            _("Dataset Created"),
            _("A Dataset was created"),
        ),
        (
            "dataset_updated",
            _("Dataset Updated"),
            _("A Dataset was updated"),
        ),
        (
            "dataset_approved",
            _("Dataset Approved"),
            _("A Dataset was approved by a Manager"),
        ),
        (
            "dataset_published",
            _("Dataset Published"),
            _("A Dataset was published"),
        ),
        (
            "dataset_deleted",
            _("Dataset Deleted"),
            _("A Dataset was deleted"),
        ),
        (
            "dataset_rated",
            _("Rating for Dataset"),
            _("A rating was given to a layer"),
        ),
    )


default_app_config = "geonode.layers.DatasetAppConfig"
