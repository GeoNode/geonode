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

from django.utils.translation import gettext_noop as _
from geonode.notifications_helper import NotificationsAppConfigBase
from django.apps import AppConfig


class DocumentsAppConfig(NotificationsAppConfigBase, AppConfig):
    name = "geonode.documents"
    NOTIFICATIONS = (
        (
            "document_created",
            _("Document Created"),
            _("A Document was created"),
        ),
        (
            "document_updated",
            _("Document Updated"),
            _("A Document was updated"),
        ),
        (
            "document_approved",
            _("Document Approved"),
            _("A Document was approved by a Manager"),
        ),
        (
            "document_published",
            _("Document Published"),
            _("A Document was published"),
        ),
        (
            "document_deleted",
            _("Document Deleted"),
            _("A Document was deleted"),
        ),
        (
            "document_rated",
            _("Rating for Document"),
            _("A rating was given to a document"),
        ),
    )
