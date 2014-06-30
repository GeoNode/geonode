from django import template

from django.db.models import Count

from agon_ratings.models import Rating
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from guardian.shortcuts import get_objects_for_user

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
    resources = get_objects_for_user(request.user, 'base.view_resourcebase')
    vectors = Layer.objects.filter(storeType='dataStore').values_list('id', flat=True)
    rasters = Layer.objects.filter(storeType='coverageStore').values_list('id', flat=True)
    remote = Layer.objects.filter(storeType='remoteStore').values_list('id', flat=True)
   
    facets['raster'] = resources.filter(id__in=vectors).count()
    facets['vector'] = resources.filter(id__in=rasters).count()
    facets['remote'] = resources.filter(id__in=remote).count()

    facet_type = context['facet_type'] if 'facet_type' in context else 'all'     
    # Break early if only_layers is set.
    if facet_type == 'layers':
        return facets


    facets['map'] = resources.filter(id__in=Map.objects.values_list('id',flat=True)).count()
    facets['document'] = resources.filter(id__in=Document.objects.values_list('id',flat=True)).count()
 
    if facet_type == 'home':
        facets['user'] = get_user_model().objects.exclude(username='AnonymousUser').count()

        facets['layer'] = facets['raster'] + facets['vector'] + facets['remote']

    return facets



