from django import template

from agon_ratings.models import Rating
from django.contrib.contenttypes.models import ContentType

register = template.Library()

@register.assignment_tag
def num_ratings(obj):
    ct = ContentType.objects.get_for_model(obj)
    return len(Rating.objects.filter(
                object_id = obj.pk,
                content_type = ct
    ))