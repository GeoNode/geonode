from django import template

from geonode.layers.models import Layer
from geonode.base.models import TopicCategory


register = template.Library()


@register.assignment_tag(takes_context=True)
def featured_layers(context, count=7):
    layers = Layer.objects.order_by("-date")[:count]
    return layers


@register.assignment_tag
def layer_categories():
    return TopicCategory.objects.all()


@register.filter(is_safe=True)
def layer_thumbnail(layer, width=159, height=63):
    return layer.thumbnail(width, height)

