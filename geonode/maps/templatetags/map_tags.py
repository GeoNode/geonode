from django import template
from geonode.layers.models import Layer
from geonode.maps.utils import *

register = template.Library()


@register.assignment_tag(takes_context=True)
def is_map_viewable_by_user(context):
    current_user = context['user']
    current_map = context['resource']
    return is_map_viewable_by_user_utils(current_user, current_map)
