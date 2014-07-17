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

""" Django signals connections and associated receiver functions for geonode's
    third-party 'social' apps which include announcements, notifications,
    relationships, actstream user_messages and potentially others
"""
import logging
from collections import defaultdict
from dialogos.models import Comment
from django.conf import settings
from django.db.models import signals
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from geonode.layers.models import Layer
from geonode.maps.models import Map
from actstream.exceptions import ModelNotActionable

logger = logging.getLogger(__name__)

activity = None
if "actstream" in settings.INSTALLED_APPS:
    from actstream import action as activity
    from actstream.actions import follow, unfollow

notification = None
if "notication" in settings.INSTALLED_APPS:
    from notification import models as notification

relationships = None
if "relationships" in settings.INSTALLED_APPS:
    relationships = True
    from relationships.models import Relationship


def activity_post_modify_object(sender, instance, created=None, **kwargs):
    """
    Creates new activities after a Map, Layer, or Comment is  created/updated/deleted.


    action_settings:
    actor: the user who performed the activity
    action_object: the object that received the action
    created_verb: a translatable verb that is used when an object is created
    deleted_verb: a translatable verb that is used when an object is deleted
    object_name: the title of the object that is used to keep information about the object after it is deleted
    target: the target of an action (if a comment is added to a map, the comment is the object the map is the target)
    updated_verb: a translatable verb that is used when an object is updated

    raw_action: a constant that describes the type of action performed (values should be: created, uploaded, deleted)
    """

    verb = None
    obj_type = instance.__class__._meta.object_name.lower()
    action_settings = defaultdict(lambda: dict(actor=getattr(instance, "owner", None),
                                               action_object=instance,
                                               created_verb=_('created'),
                                               deleted_verb=_('deleted'),
                                               object_name=getattr(instance, 'name', None),
                                               target=None,
                                               updated_verb=_('updated'),
                                               ))

    action_settings['map'].update(object_name=getattr(instance, 'title', None),)
    action_settings['comment'].update(actor=getattr(instance, 'author', None),
                                      created_verb=_("added a comment"),
                                      target=getattr(instance, 'content_object', None),
                                      updated_verb=_("updated a comment"),
                                      )
    action_settings['layer'].update(created_verb=_('uploaded'))

    action = action_settings[obj_type]
    if created:
        # object was created
        verb = action.get('created_verb')
        raw_action = 'created'

    else:
        if created is False:
            # object was saved.
            if not isinstance(instance, Layer) and not isinstance(instance, Map):
                verb = action.get('updated_verb')
                raw_action = 'updated'

        if created is None:
            # object was deleted.
            verb = action.get('deleted_verb')
            raw_action = 'deleted'
            action.update(action_object=None,
                          target=None)

    if verb:
        try:
            activity.send(action.get('actor'),
                          verb='{verb}'.format(verb=verb),
                          action_object=action.get('action_object'),
                          target=action.get('target', None),
                          object_name=action.get('object_name'),
                          raw_action=raw_action,
                          )
        except ModelNotActionable:
            logger.debug('The activity received a non-actionable Model or None as the actor/action.')


def notification_post_save_layer(instance, sender, created, **kwargs):
    if created:
        superusers = get_user_model().objects.filter(is_superuser=True)
        notification.queue(superusers, "layer_uploaded", {"from_user": instance.owner})
    else:
        # Notification if existing layer is updated
        pass


def relationship_post_save_actstream(instance, sender, created, **kwargs):
    follow(instance.from_user, instance.to_user)


def relationship_pre_delete_actstream(instance, sender, **kwargs):
    unfollow(instance.from_user, instance.to_user)


def relationship_post_save(instance, sender, created, **kwargs):
    notification.queue([instance.to_user], "user_follow", {"from_user": instance.from_user})

if activity:
    signals.post_save.connect(activity_post_modify_object, sender=Comment)
    signals.post_save.connect(activity_post_modify_object, sender=Layer)
    signals.post_delete.connect(activity_post_modify_object, sender=Layer)

    signals.post_save.connect(activity_post_modify_object, sender=Map)
    signals.post_delete.connect(activity_post_modify_object, sender=Map)

if notification:
    signals.post_save.connect(notification_post_save_layer, sender=Layer)
if relationships and activity:
    signals.post_save.connect(relationship_post_save_actstream, sender=Relationship)
    signals.pre_delete.connect(relationship_pre_delete_actstream, sender=Relationship)
if relationships and notification:
    signals.post_save.connect(relationship_post_save, sender=Relationship)
