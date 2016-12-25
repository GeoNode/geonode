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

from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _
import logging
logger = logging.getLogger(__name__)

if "notification" in settings.INSTALLED_APPS:
    import notification

    if hasattr(notification, 'models'):
        def create_notice_types(app, created_models, verbosity, **kwargs):
            notification.models.NoticeType.create(
                "document_created",
                _("Document Created"),
                _("A Document was created"))
            notification.models.NoticeType.create(
                "document_updated",
                _("Document Updated"),
                _("A Document was updated"))
            notification.models.NoticeType.create(
                "document_deleted",
                _("Document Deleted"),
                _("A Document was deleted"))
            notification.models.NoticeType.create(
                "document_comment",
                _("Comment on Document"),
                _("A Document was commented on"))
            notification.models.NoticeType.create(
                "document_rated",
                _("Document for Map"),
                _("A rating was given to a document"))

        signals.post_migrate.connect(
            create_notice_types,
            sender=notification.models)
        logger.info(
            "Notifications Configured for geonode.documents.management.commands")
else:
    logger.info(
        "Skipping creation of NoticeTypes for geonode.documents.management.commands,"
        " since notification app was not found.")
