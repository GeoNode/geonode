from django import template

from geonode.maps.models import Map


register = template.Library()


@register.assignment_tag(takes_context=True)
def featured_maps(context, count=7):
    maps = Map.objects.order_by("-last_modified")[:count]
    return maps
