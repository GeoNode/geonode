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

""" Django signals connections and associated receiver functions for geonode's
    third-party 'social' apps which include announcements, notifications,
    relationships, actstream user_messages and potentially others
"""
import logging
import datetime
from collections import defaultdict
from dialogos.models import Comment

from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _

# from actstream.exceptions import ModelNotActionable

from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.notifications_helper import (send_notification, queue_notification,
                                          has_notifications, get_notification_recipients)

logger = logging.getLogger(__name__)

activity = None
if "actstream" in settings.INSTALLED_APPS:
    from actstream import action as activity
    from actstream.actions import follow, unfollow

relationships = None
if "relationships" in settings.INSTALLED_APPS:
    relationships = True
    from relationships.models import Relationship

ratings = None
if "ratings" in settings.INSTALLED_APPS:
    ratings = True
    from agon_ratings.models import Rating


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

    try:
        action_settings['map'].update(object_name=getattr(instance, 'title', None),)
    except Exception as e:
        logger.exception(e)

    action_settings['comment'].update(actor=getattr(instance, 'author', None),
                                      created_verb=_("added a comment"),
                                      target=getattr(instance, 'content_object', None),
                                      updated_verb=_("updated a comment"),
                                      )
    action_settings['layer'].update(created_verb=_('uploaded'))
    action_settings['document'].update(created_verb=_('uploaded'))

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
                          verb=u"{verb}".format(verb=verb),
                          action_object=action.get('action_object'),
                          target=action.get('target', None),
                          object_name=action.get('object_name'),
                          raw_action=raw_action,
                          )
        # except ModelNotActionable:
        except BaseException:
            logger.debug('The activity received a non-actionable Model or None as the actor/action.')


def relationship_post_save_actstream(instance, sender, created, **kwargs):
    follow(instance.from_user, instance.to_user)


def relationship_pre_delete_actstream(instance, sender, **kwargs):
    unfollow(instance.from_user, instance.to_user)


def relationship_post_save(instance, sender, created, **kwargs):
    queue_notification([instance.to_user], "user_follow", {"from_user": instance.from_user})


if activity:
    signals.post_save.connect(activity_post_modify_object, sender=Comment)
    signals.post_save.connect(activity_post_modify_object, sender=Layer)
    signals.post_delete.connect(activity_post_modify_object, sender=Layer)

    signals.post_save.connect(activity_post_modify_object, sender=Map)
    signals.post_delete.connect(activity_post_modify_object, sender=Map)

    signals.post_save.connect(activity_post_modify_object, sender=Document)
    signals.post_delete.connect(activity_post_modify_object, sender=Document)


def notification_post_save_resource(instance, sender, created, **kwargs):
    """ Send a notification when a layer, map or document is created or
    updated
    """
    notice_type_label = '%s_created' if created else '%s_updated'
    notice_type_label = notice_type_label % instance.class_name.lower()
    recipients = get_notification_recipients(notice_type_label)
    send_notification(recipients, notice_type_label, {'resource': instance})

    # Approval Notifications Here
    if settings.ADMIN_MODERATE_UPLOADS:
        if instance.is_approved and not instance.is_published:
            notice_type_label = '%s_approved'
            notice_type_label = notice_type_label % instance.class_name.lower()
            recipients = get_notification_recipients(notice_type_label)
            send_notification(recipients, notice_type_label, {'resource': instance})

    # Publishing Notifications Here
    if settings.RESOURCE_PUBLISHING:
        if instance.is_approved and instance.is_published:
            notice_type_label = '%s_published'
            notice_type_label = notice_type_label % instance.class_name.lower()
            recipients = get_notification_recipients(notice_type_label)
            send_notification(recipients, notice_type_label, {'resource': instance})


def notification_post_delete_resource(instance, sender, **kwargs):
    """ Send a notification when a layer, map or document is deleted
    """
    notice_type_label = '%s_deleted' % instance.class_name.lower()
    recipients = get_notification_recipients(notice_type_label)
    send_notification(recipients, notice_type_label, {'resource': instance})


def rating_post_save(instance, sender, created, **kwargs):
    """ Send a notification when rating a layer, map or document
    """
    notice_type_label = '%s_rated' % instance.content_object.class_name.lower()
    recipients = get_notification_recipients(notice_type_label, instance.user)
    send_notification(recipients, notice_type_label, {"instance": instance})


def comment_post_save(instance, sender, created, **kwargs):
    """ Send a notification when a comment to a layer, map or document has
    been submitted
    """
    notice_type_label = '%s_comment' % instance.content_object.class_name.lower()
    recipients = get_notification_recipients(notice_type_label, instance.author)
    send_notification(recipients, notice_type_label, {"instance": instance})


# signals
# layer/map/document notifications
for resource in (Layer, Map, Document):
    signals.post_save.connect(notification_post_save_resource, sender=resource)
    signals.post_delete.connect(notification_post_delete_resource, sender=resource)

signals.post_save.connect(comment_post_save, sender=Comment)

# rating notifications
if ratings and has_notifications:
    signals.post_save.connect(rating_post_save, sender=Rating)
if relationships and activity:
    signals.post_save.connect(relationship_post_save_actstream, sender=Relationship)
    signals.pre_delete.connect(relationship_pre_delete_actstream, sender=Relationship)
if relationships and has_notifications:
    signals.post_save.connect(relationship_post_save, sender=Relationship)


def json_serializer_producer(dictionary):
    output = {}
    # pop no useful information for others services which wants to connect to geonode
    if 'supplemental_information_en' in dictionary.keys():
        dictionary.pop('supplemental_information_en', None)
    if 'supplemental_information' in dictionary.keys():
        dictionary.pop('supplemental_information', None)
    if 'doc_file' in dictionary.keys():
        file_object = dictionary['doc_file']
        dictionary['doc_file'] = str(file_object)
    if 'regions' in dictionary.keys():
        keys = dictionary['regions']
        dictionary['regions'] = str(keys)
    if 'keywords' in dictionary.keys():
        keys = dictionary['keywords']
        dictionary['keywords'] = str(keys)
    if 'tkeywords' in dictionary.keys():
        keys = dictionary['tkeywords']
        dictionary['tkeywords'] = str(keys)
    if 'styles' in dictionary.keys():
        keys = dictionary['styles']
        dictionary['styles'] = str(keys)
    if 'contacts' in dictionary.keys():
        keys = dictionary['contacts']
        dictionary['contacts'] = str(keys)
    for (x, y) in dictionary.items():
        if not y:
            # this is used to solve
            # TypeError: [] is not JSON serializable when it is null
            y = str(y)
        # check datetime object
        # TODO: Use instanceof
        if isinstance(y, datetime.datetime):
            y = str(y)

        output[x] = y
    return output
