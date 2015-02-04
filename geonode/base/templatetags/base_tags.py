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
    title_filter = request.GET.get('title__icontains', '')
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

        text = Document.objects.filter(doc_type='text').filter(
            title__icontains=title_filter).values_list('id', flat=True)
        image = Document.objects.filter(doc_type='image').filter(
            title__icontains=title_filter).values_list('id', flat=True)
        presentation = Document.objects.filter(doc_type='presentation').filter(
            title__icontains=title_filter).values_list('id', flat=True)
        archive = Document.objects.filter(doc_type='archive').filter(
            title__icontains=title_filter).values_list('id', flat=True)
        other = Document.objects.filter(doc_type='other').filter(
            title__icontains=title_filter).values_list('id', flat=True)

        if settings.SKIP_PERMS_FILTER:
            facets['text'] = text.count()
            facets['image'] = image.count()
            facets['presentation'] = presentation.count()
            facets['archive'] = archive.count()
            facets['other'] = other.count()
        else:
            resources = get_objects_for_user(
                request.user, 'base.view_resourcebase')
            facets['text'] = resources.filter(id__in=text).count()
            facets['image'] = resources.filter(id__in=image).count()
            facets['presentation'] = resources.filter(
                id__in=presentation).count()
            facets['archive'] = resources.filter(id__in=archive).count()
            facets['other'] = resources.filter(id__in=other).count()

            return facets

    else:

        facets = {
            'raster': 0,
            'vector': 0,
        }

        vectors = Layer.objects.filter(storeType='dataStore').filter(
            title__icontains=title_filter).values_list('id', flat=True)
        rasters = Layer.objects.filter(storeType='coverageStore').filter(
            title__icontains=title_filter).values_list('id', flat=True)
        remote = Layer.objects.filter(storeType='remoteStore').filter(
            title__icontains=title_filter).values_list('id', flat=True)

        if settings.RESOURCE_PUBLISHING:
            vectors = vectors.filter(is_published=True)
            rasters = rasters.filter(is_published=True)
            remote = remote.filter(is_published=True)

        if settings.SKIP_PERMS_FILTER:
            facets['raster'] = rasters.count()
            facets['vector'] = vectors.count()
            facets['remote'] = remote.count()
        else:
            resources = get_objects_for_user(
                request.user, 'base.view_resourcebase').filter(title__icontains=title_filter)
            facets['raster'] = resources.filter(id__in=rasters).count()
            facets['vector'] = resources.filter(id__in=vectors).count()
            facets['remote'] = resources.filter(id__in=remote).count()

        facet_type = context[
            'facet_type'] if 'facet_type' in context else 'all'
        # Break early if only_layers is set.
        if facet_type == 'layers':
            return facets

        if settings.SKIP_PERMS_FILTER:
            facets['map'] = Map.objects.filter(
                title__icontains=title_filter).count()
            facets['document'] = Document.objects.filter(
                title__icontains=title_filter).count()
        else:
            facets['map'] = resources.filter(title__icontains=title_filter).filter(
                id__in=Map.objects.values_list('id', flat=True)).count()
            facets['document'] = resources.filter(title__icontains=title_filter).filter(
                id__in=Document.objects.values_list('id', flat=True)).count()

        if facet_type == 'home':
            facets['user'] = get_user_model().objects.exclude(
                username='AnonymousUser').count()

            facets['layer'] = facets['raster'] + \
                facets['vector'] + facets['remote']

    return facets
