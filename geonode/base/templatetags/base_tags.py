from django import template

from agon_ratings.models import Rating
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db.models import Count

from guardian.shortcuts import get_objects_for_user
#from geonode import settings
from django.conf import settings

from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.groups.models import GroupProfile

import urllib2
from urllib2 import HTTPError
import json
from django.core.urlresolvers import resolve
from django.db.models import Q
from geoserver.catalog import Catalog

import geonode.settings as settings

register = template.Library()

@register.inclusion_tag('phil-ext.html',takes_context=True)
def get_public_location(context):
    public_location = str(settings.OGC_SERVER['default']['PUBLIC_LOCATION'])
    return public_location

@register.assignment_tag
def get_orthophotos(takes_context=True):
    orthophotos = Layer.objects.get(name='orthophotos_resampled')
    return str(orthophotos.typename)

@register.inclusion_tag('index.html',takes_context=True)
def get_philgrid(context):
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
                username=settings.OGC_SERVER['default']['USER'],
                password=settings.OGC_SERVER['default']['PASSWORD'])
    philgrid = Layer.objects.get(name__icontains="philgrid")
    # resource = philgrid.resource
    gs_layer = cat.get_layer(philgrid.name)
    resource = gs_layer.resource
    return resource

@register.assignment_tag
def get_fhm_count(takes_context=True):
    try:
        visit_url = 'https://lipad-fmc.dream.upd.edu.ph/api/layers/' #?keyword__contains=hazard'
        response = urllib2.urlopen(visit_url)
        data = json.loads(response.read())
        fhm_count = data['meta']['total_count']
    except:
        fhm_count = "N/A"
    return fhm_count

@register.assignment_tag
def get_resourceLayers_count(takes_context=True):
    urls_to_visit = [links for links in settings.LIPAD_INSTANCES if links != 'https://lipad-fmc.dream.upd.edu.ph/']
    rl_count = Layer.objects.filter(keywords__name__icontains="phillidar2").count()
    for visit_url in urls_to_visit:
        try:
            response = urllib2.urlopen(visit_url+'api/total_count', timeout = 1)
            data = json.loads(response.read())
            rl_count += data['total_count']
        except:
            rl_count += 0
    return rl_count

@register.assignment_tag
def get_fhm_fmc_url(takes_context=True):
    fhm = settings.LIPAD_FMC_FHM_URL
    return fhm

@register.assignment_tag
def get_public_location(takes_context=True):
    pl = settings.OGC_SERVER['default']['PUBLIC_LOCATION']
    return pl

@register.assignment_tag
def num_ratings(obj):
    ct = ContentType.objects.get_for_model(obj)
    return len(Rating.objects.filter(object_id=obj.pk, content_type=ct))


@register.assignment_tag(takes_context=True)
def facets(context):
    request = context['request']
    title_filter = request.GET.get('title__icontains', '')

    facet_type = context['facet_type'] if 'facet_type' in context else 'all'

    if not settings.SKIP_PERMS_FILTER:
        authorized = get_objects_for_user(
            request.user, 'base.view_resourcebase').values('id')

    if facet_type == 'documents':

        documents = Document.objects.filter(title__icontains=title_filter)

        if settings.RESOURCE_PUBLISHING:
            documents = documents.filter(is_published=True)

        if not settings.SKIP_PERMS_FILTER:
            documents = documents.filter(id__in=authorized)

        counts = documents.values('doc_type').annotate(count=Count('doc_type'))
        facets = dict([(count['doc_type'], count['count']) for count in counts])

        return facets

    else:

        layers = Layer.objects.filter(title__icontains=title_filter)

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

        maps = Map.objects.filter(title__icontains=title_filter)
        documents = Document.objects.filter(title__icontains=title_filter)

        if not settings.SKIP_PERMS_FILTER:
            maps = maps.filter(id__in=authorized)
            documents = documents.filter(id__in=authorized)

        facets['map'] = maps.count()
        facets['document'] = documents.count()

        if facet_type == 'home':
            facets['user'] = get_user_model().objects.exclude(
                username='AnonymousUser').count()

            facets['group'] = GroupProfile.objects.exclude(
                access="private").count()

            facets['layer'] = facets['raster'] + \
                facets['vector'] + facets['remote']

    return facets
