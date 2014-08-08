from django import template

from agon_ratings.models import Rating
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from guardian.shortcuts import get_objects_for_user
from geonode import settings

from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document

register = template.Library()


@register.assignment_tag
def num_ratings(obj):
    ct = ContentType.objects.get_for_model(obj)
    return len(Rating.objects.filter(object_id=obj.pk, content_type=ct))


@register.assignment_tag(takes_context=True)
def facets(context):
    request = context['request']

    facets = {}

    facet_type = context['facet_type'] if 'facet_type' in context else 'all'
    if facet_type == 'documents':

        facets = {
            'text': 0,
            'image': 0,
            'presentation': 0,
            'archive': 0,
            'other': 0
        }

        text = Document.objects.filter(doc_type='text').values_list('id', flat=True)
        image = Document.objects.filter(doc_type='image').values_list('id', flat=True)
        presentation = Document.objects.filter(doc_type='presentation').values_list('id', flat=True)
        archive = Document.objects.filter(doc_type='archive').values_list('id', flat=True)
        other = Document.objects.filter(doc_type='other').values_list('id', flat=True)

        if settings.SKIP_PERMS_FILTER:
            facets['text'] = text.count()
            facets['image'] = image.count()
            facets['presentation'] = presentation.count()
            facets['archive'] = archive.count()
            facets['other'] = other.count()
        else:
            resources = get_objects_for_user(request.user, 'base.view_resourcebase')
            facets['text'] = resources.filter(id__in=text).count()
            facets['image'] = resources.filter(id__in=image).count()
            facets['presentation'] = resources.filter(id__in=presentation).count()
            facets['archive'] = resources.filter(id__in=archive).count()
            facets['other'] = resources.filter(id__in=other).count()

            return facets

    else:

        facets = {
            'raster': 0,
            'vector': 0,
        }

        vectors = Layer.objects.filter(storeType='dataStore').values_list('id', flat=True)
        rasters = Layer.objects.filter(storeType='coverageStore').values_list('id', flat=True)
        remote = Layer.objects.filter(storeType='remoteStore').values_list('id', flat=True)

        if settings.SKIP_PERMS_FILTER:
            facets['raster'] = rasters.count()
            facets['vector'] = vectors.count()
            facets['remote'] = remote.count()
        else:
            resources = get_objects_for_user(request.user, 'base.view_resourcebase')
            facets['raster'] = resources.filter(id__in=rasters).count()
            facets['vector'] = resources.filter(id__in=vectors).count()
            facets['remote'] = resources.filter(id__in=remote).count()

        facet_type = context['facet_type'] if 'facet_type' in context else 'all'
        # Break early if only_layers is set.
        if facet_type == 'layers':
            return facets

        if settings.SKIP_PERMS_FILTER:
            facets['map'] = Map.objects.all().count()
            facets['document'] = Document.objects.all().count()
        else:
            facets['map'] = resources.filter(id__in=Map.objects.values_list('id', flat=True)).count()
            facets['document'] = resources.filter(id__in=Document.objects.values_list('id', flat=True)).count()

        if facet_type == 'home':
            facets['user'] = get_user_model().objects.exclude(username='AnonymousUser').count()

            facets['layer'] = facets['raster'] + facets['vector'] + facets['remote']

    return facets
