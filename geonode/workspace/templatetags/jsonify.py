from django.utils.safestring import mark_safe
from django import template
import json

register = template.Library()


@register.simple_tag
def jsonify(obj):

    return mark_safe(json.dumps(obj))

