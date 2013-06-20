from django import template
 
from geonode.base.models import TopicCategory

from geonode.documents.models import Document


register = template.Library()


@register.assignment_tag(takes_context=True)
def featured_layers(context, count=7):
    documents = Document.objects.order_by("-date")[:count]
    return documents


@register.assignment_tag
def document_categories():
    return TopicCategory.objects.all()
