#########################################################################
#
# Copyright (C) 2012 OpenPlans
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
                "layer_created",
                _("StoryLayer Created"),
                _("A StoryLayer was created"))
            notification.models.NoticeType.create(
                "layer_updated",
                _("StoryLayer Updated"),
                _("A StoryLayer was updated"))
            notification.models.NoticeType.create(
                "layer_deleted",
                _("StoryLayer Deleted"),
                _("A StoryLayer was deleted"))
            notification.models.NoticeType.create(
                "layer_comment",
                _("Comment on StoryLayer"),
                _("A StoryLayer was commented on"))
            notification.models.NoticeType.create(
                "layer_rated",
                _("Rating for StoryLayer"),
                _("A rating was given to a StoryLayer"))
            notification.models.NoticeType.create(
                "layer_favorited",
                _("StoryLayer favorited"),
                _("A StoryLayer was favorited"))
            notification.models.NoticeType.create(
                "layer_flagged",
                _("StoryLayer flagged"),
                _("A flag was given to a StoryLayer"))
            notification.models.NoticeType.create(
                "layer_downloaded",
                _("StoryLayer downloaded"),
                _("StoryLayer downloaded by another user"))
            notification.models.NoticeType.create(
                "layer_used",
                _("StoryLayer used in a MapStory"),
                _("Your StoryLayer was used in someone else's MapStory"))


        signals.post_syncdb.connect(
            create_notice_types,
            sender=notification.models)
        logger.info(
            "Notifications Configured for geonode.layers.management.commands")
else:
    logger.info(
        "Skipping creation of NoticeTypes for geonode.layers.management.commands,"
        " since notification app was not found.")
