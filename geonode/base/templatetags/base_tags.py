from django import template

from django.db.models import Count

from agon_ratings.models import Rating
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

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

    facets = {
        'raster': 0,
        'vector': 0,
    }

    for layer in Layer.objects.all():
        if request.user.has_perm('layers.view_layer', layer):
            if layer.storeType == 'coverageStore':
                facets['raster'] += 1
            else:
                facets['vector'] +=1

    facet_type = context['facet_type'] if 'facet_type' in context else 'all'     
    # Break early if only_layers is set.
    if facet_type == 'layers':
        return facets


    facets['map'] = 0
    for the_map in Map.objects.all():
        if request.user.has_perm('maps.view_map', the_map):
            facets['map'] +=1

    facets['document'] = 0
    for doc in Document.objects.all():
        if request.user.has_perm('document.view_document', doc):
            facets['document'] += 1

    if facet_type == 'home':
        facets['user'] = User.objects.count()

        facets['layer'] = facets['raster'] + facets['vector']

    return facets



