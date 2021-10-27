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

import json
import logging
from django import template
from django.utils.translation import ugettext_lazy as _

from geonode.utils import get_subclasses_by_model

register = template.Library()
logger = logging.getLogger(__name__)


def get_data(action, key, default=None):
    """
    Checks for a key in the action's JSON data field.  Returns default if the key does not exist.
    """

    if hasattr(action, 'data') and action.data:
        if hasattr(action.data, 'get'):
            return action.data.get(key, default)
        elif action and action.data:
            _action_data = json.loads(action.data)
            if isinstance(_action_data, str):
                return _action_data
            else:
                try:
                    return _action_data.get(key, default)
                except Exception as e:
                    logger.exceprion(e)
    return default


@register.inclusion_tag('social/_activity_item.html')
def activity_item(action, **kwargs):
    """
    Provides a location to manipulate an action in preparation for display.
    """
    actor = action.actor
    activity_class = 'activity'
    verb = action.verb
    username = actor.username if actor else "someone"
    target = action.target
    object_type = None
    object = action.action_object
    raw_action = get_data(action, 'raw_action')
    object_name = get_data(action, 'object_name')
    preposition = _("to")
    fragment = None

    if object:
        object_type = object.__class__._meta.object_name.lower()

    if target:
        target_type = target.__class__._meta.object_name.lower()  # noqa

    # Set the item's class based on the object.
    if object:
        geoapps = [app.lower() for app in get_subclasses_by_model('GeoApp')]
        if object_type in geoapps:
            activity_class = object_type

        if object_type == 'comment':
            activity_class = 'comment'
            preposition = _("on")
            object = None
            fragment = "comments"

        if object_type == 'map':
            activity_class = 'map'

        if object_type == 'layer':
            activity_class = 'layer'

        if object_type == 'document':
            activity_class = 'document'

    if raw_action == 'deleted':
        activity_class = 'delete'

    if raw_action == 'created' and \
            object_type in ('layer', 'document'):
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
        fragment=fragment
    )
    return ctx
