from django import template

from django.db.models import Count

from agon_ratings.models import Rating
from django.contrib.contenttypes.models import ContentType

from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document

register = template.Library()

@register.assignment_tag
def num_ratings(obj):
    ct = ContentType.objects.get_for_model(obj)
    return len(Rating.objects.filter(
                object_id = obj.pk,
                content_type = ct
    ))
    

@register.assignment_tag(takes_context=True)
def facets(context):
    request = context['request']
    path = request.path
    facets = {
        'raster': 0,
        'vector': 0,
        'map': 0,
        'document': 0,
    }
    
    if 'layers' in path or 'search' in path:
        for layer in Layer.objects.all():
            if request.user.has_perm('layers.view_layer', layer):
                if layer.storeType == 'coverageStore':
                    facets['raster'] += 1
                else:
                    facets['vector'] +=1

    if 'search' in path:                
        for the_map in Map.objects.all():
            if request.user.has_perm('maps.view_map', the_map):
                facets['map'] +=1

        for doc in Document.objects.all():
            if request.user.has_perm('document.view_document', doc):
                facets['document'] += 1        

    return facets



