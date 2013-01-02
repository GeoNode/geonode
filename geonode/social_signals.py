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

from django.conf import settings
from django.db.models import signals
from django.contrib.auth.models import User

from geonode.layers.models import Layer

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

def activity_post_save_layer(sender, instance, created, **kwargs):
    if created:
        activity.send(instance.owner, verb='uploaded layer', target=instance)
    else:
        # Action if existing layer is updated
        pass

def notification_post_save_layer(instance, sender, created, **kwargs):
    if created: 
        superusers = User.objects.filter(is_superuser=True)
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
    signals.post_save.connect(activity_post_save_layer, sender=Layer)
if notification:
    signals.post_save.connect(notification_post_save_layer, sender=Layer)
if relationships and activity:
    signals.post_save.connect(relationship_post_save_actstream, sender=Relationship)
    signals.pre_delete.connect(relationship_pre_delete_actstream, sender=Relationship)
if relationships and notification:
    signals.post_save.connect(relationship_post_save, sender=Relationship)
