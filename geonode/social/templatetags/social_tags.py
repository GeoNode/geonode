from django import template
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
register = template.Library()

def get_data(action, key, default=None):
    """
    Checks for a key in the action's JSON data field.  Returns default if the key does not exist.
    """

    if hasattr(action, 'data') and action.data:
        return action.data.get(key, default)
    else:
        return default

@register.inclusion_tag('social/_activity_item.html')
def activity_item(action, **kwargs):
    """
    Provides a location to manipulate an action in preparation for display.
    """

    actor = action.actor
    activity_class = 'activity'
    verb = action.verb
    username = actor.profile.name or actor.username
    target = action.target
    object_type = None
    object = action.action_object
    raw_action = get_data(action, 'raw_action')
    object_name = get_data(action, 'object_name')
    preposition = _("to")

    if object:
        object_type = object.__class__._meta.object_name.lower()

    if target:
        target_type = target.__class__._meta.object_name.lower()

    if actor is None:
        return str()

    # Set the item's class based on the object.
    if object:
        if object_type == 'comment':
            activity_class = 'comment'
            preposition = _("on")
            object = None

        if object_type == 'map':
            activity_class = 'map'

        if object_type == 'layer':
            activity_class = 'layer'

    if raw_action == 'deleted':
        activity_class = 'delete'

    if raw_action == 'created' and object_type == 'layer':
        activity_class = 'upload'

    ctx = dict(
        activity_class=activity_class,
        action=action,
        actor=actor,
        object=object,
        object_name=object_name,
        preposition=preposition,
        target=target,
        timestamp=action.timestamp,
        username=username,
        verb=verb,
    )
    return ctx