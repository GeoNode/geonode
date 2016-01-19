from django import template

from geonode.layers.models import Layer


register = template.Library()


@register.assignment_tag(takes_context=True)
def featured_layers(context, count=7):
    layers = Layer.objects.order_by("-date")[:count]
    return layers


@register.filter(is_safe=True)
def layer_thumbnail(layer, width=159, height=63):
    return layer.thumbnail(width, height)
