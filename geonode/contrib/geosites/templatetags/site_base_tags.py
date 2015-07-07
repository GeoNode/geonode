from django import template

from django.contrib.auth import get_user_model
from django.db.models import Count

from guardian.shortcuts import get_objects_for_user
from geonode import settings

from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.groups.models import GroupProfile

from geonode.contrib.geosites.utils import resources_for_site, users_for_site


register = template.Library()


@register.assignment_tag(takes_context=True)
def site_facets(context):
    request = context['request']
    title_filter = request.GET.get('title__icontains', '')

    facet_type = context['facet_type'] if 'facet_type' in context else 'all'

    if not settings.SKIP_PERMS_FILTER:
        authorized = get_objects_for_user(
            request.user, 'base.view_resourcebase').values('id')

    if facet_type == 'documents':

        documents = Document.objects.filter(title__icontains=title_filter).filter(id__in=resources_for_site())

        if settings.RESOURCE_PUBLISHING:
            documents = documents.filter(is_published=True)

        if not settings.SKIP_PERMS_FILTER:
            documents = documents.filter(id__in=authorized)

        counts = documents.values('doc_type').annotate(count=Count('doc_type'))
        facets = dict([(count['doc_type'], count['count']) for count in counts])

        return facets

    else:

        layers = Layer.objects.filter(title__icontains=title_filter).filter(id__in=resources_for_site())

        if settings.RESOURCE_PUBLISHING:
            layers = layers.filter(is_published=True)

        if not settings.SKIP_PERMS_FILTER:
            layers = layers.filter(id__in=authorized)

        counts = layers.values('storeType').annotate(count=Count('storeType'))
        count_dict = dict([(count['storeType'], count['count']) for count in counts])

        facets = {
            'raster': count_dict.get('coverageStore', 0),
            'vector': count_dict.get('dataStore', 0),
            'remote': count_dict.get('remoteStore', 0),
        }

        # Break early if only_layers is set.
        if facet_type == 'layers':
            return facets

        maps = Map.objects.filter(title__icontains=title_filter).filter(id__in=resources_for_site())
        documents = Document.objects.filter(title__icontains=title_filter).filter(id__in=resources_for_site())

        if not settings.SKIP_PERMS_FILTER:
            maps = maps.filter(id__in=authorized)
            documents = documents.filter(id__in=authorized)

        facets['map'] = maps.count()
        facets['document'] = documents.count()

        if facet_type == 'home':
            facets['user'] = get_user_model().objects.exclude(
                username='AnonymousUser').filter(id__in=users_for_site()).count()

            facets['group'] = GroupProfile.objects.exclude(
                access="private").count()

            facets['layer'] = facets['raster'] + \
                facets['vector'] + facets['remote']
    return facets
