from django import template

from geonode.layers.models import Layer


register = template.Library()


@register.assignment_tag(takes_context=True)
def featured_layers(context, count=7):
    request = context["request"]
    layers = Layer.objects.order_by("-date")[:count]
    return layers
