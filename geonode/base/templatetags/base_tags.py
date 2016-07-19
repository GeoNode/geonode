# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django import template

from agon_ratings.models import Rating
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db.models import Count

from guardian.shortcuts import get_objects_for_user
from geonode import settings

from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.groups.models import GroupProfile

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

            facets['group'] = GroupProfile.objects.exclude(
                access="private").count()

            facets['layer'] = facets['raster'] + \
                facets['vector'] + facets['remote']

    return facets


@register.assignment_tag(takes_context=True)
def get_current_path(context):
    request = context['request']
    return request.get_full_path()


@register.assignment_tag(takes_context=True)
def get_context_resourcetype(context):
    c_path = get_current_path(context)
    if c_path.find('/layers/') > - 1:
        return 'layers'
    elif c_path.find('/maps/') > - 1:
        return 'maps'
    elif c_path.find('/documents/') > - 1:
        return 'documents'
    elif c_path.find('/search/') > - 1:
        return 'search'
    else:
        return 'error'
    return get_current_path(context)


@register.assignment_tag(takes_context=True)
def user_can_add_resource_base(context):
    request = context['request']
    gs = request.user.groups.all()
    list_auth_add_resource_base = []
    can_add_ressource = False
    for g in gs:
        list_auth_add_resource_base.append([g.name, len(g.permissions.all().filter(codename='add_resourcebase'))])
        if len(g.permissions.all().filter(codename='add_resourcebase')) == 1:
            can_add_ressource = True
    if request.user.is_superuser:
        can_add_ressource = True
    return can_add_ressource


@register.assignment_tag(takes_context=True)
def user_can_change_perms(context):
    request = context['request']
    gs = request.user.groups.all()
    list_auth_change_perms = []
    can_change_perms = False
    for g in gs:
        list_auth_change_perms.append([g.name, len(g.permissions.all().filter(codename='change_resourcebase'))])
        if len(g.permissions.all().filter(codename='change_resourcebase')) == 1:
            can_change_perms = True
    if request.user.is_superuser:
        can_change_perms = True
    return can_change_perms
