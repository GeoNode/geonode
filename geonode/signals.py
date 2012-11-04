from django.conf import settings
from django.db.models import signals

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

if activity:
    signals.post_save.connect(activity_post_save_layer, sender=Layer)
if notification:
    signals.post_save.connect(notification_post_save_layer, sender=Layer)
if relationships and activity:
    signals.post_save.connect(relationship_post_save_actstream, sender=Relationship)
    signals.pre_delete.connect(relationship_pre_delete_actstream, sender=Relationship)
