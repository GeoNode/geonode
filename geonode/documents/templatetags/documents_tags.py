from django import template
 
from geonode.documents.models import Document


register = template.Library()


@register.assignment_tag(takes_context=True)
def featured_layers(context, count=7):
    documents = Document.objects.order_by("-date")[:count]
    return documents
