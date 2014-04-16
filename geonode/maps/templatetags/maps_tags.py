from django import template

from geonode.maps.models import Map
from geonode.search.search import _filter_security

register = template.Library()


@register.assignment_tag(takes_context=True)
def featured_maps(context, count=7):
    request = context['request']
    maps = Map.objects.order_by("-last_modified")
    maps = _filter_security(maps, request.user, Map, 'view_map')[:count]
    return maps
