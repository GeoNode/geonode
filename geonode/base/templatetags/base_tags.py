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
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Count
from django.conf import settings

from guardian.shortcuts import get_objects_for_user

from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.groups.models import GroupProfile
from geonode.base.models import HierarchicalKeyword

register = template.Library()


@register.assignment_tag
def num_ratings(obj):
    ct = ContentType.objects.get_for_model(obj)
    return len(Rating.objects.filter(object_id=obj.pk, content_type=ct))


@register.assignment_tag(takes_context=True)
def facets(context):
    request = context['request']
    is_admin = False
    is_staff = False
    is_manager = False
    if request.user:
        is_admin = request.user.is_superuser if request.user else False
        is_staff = request.user.is_staff if request.user else False
        try:
            is_manager = request.user.groupmember_set.all().filter(role='manager').exists()
        except:
            is_manager = False

    title_filter = request.GET.get('title__icontains', '')
    extent_filter = request.GET.get('extent', None)
    keywords_filter = request.GET.getlist('keywords__slug__in', None)
    category_filter = request.GET.getlist('category__identifier__in', None)
    regions_filter = request.GET.getlist('regions__name__in', None)
    owner_filter = request.GET.getlist('owner__username__in', None)
    date_gte_filter = request.GET.get('date__gte', None)
    date_lte_filter = request.GET.get('date__lte', None)
    date_range_filter = request.GET.get('date__range', None)

    facet_type = context['facet_type'] if 'facet_type' in context else 'all'

    if not settings.SKIP_PERMS_FILTER:
        authorized = get_objects_for_user(
            request.user, 'base.view_resourcebase').values('id')

    if facet_type == 'documents':

        documents = Document.objects.filter(title__icontains=title_filter)

        if category_filter:
            documents = documents.filter(category__identifier__in=category_filter)

        if regions_filter:
            documents = documents.filter(regions__name__in=regions_filter)

        if owner_filter:
            documents = documents.filter(owner__username__in=owner_filter)

        if date_gte_filter:
            documents = documents.filter(date__gte=date_gte_filter)
        if date_lte_filter:
            documents = documents.filter(date__lte=date_lte_filter)
        if date_range_filter:
            documents = documents.filter(date__range=date_range_filter.split(','))

        if settings.ADMIN_MODERATE_UPLOADS:
            if not is_admin and not is_staff:
                if is_manager:
                    groups = request.user.groups.all()
                    group_list_all = request.user.group_list_all().values('group')
                    public_groups = GroupProfile.objects.exclude(access="private").values('group')
                    try:
                        anonymous_group = Group.objects.get(name='anonymous')
                        documents = documents.filter(
                            Q(group__isnull=True) | Q(group__in=groups) |
                            Q(group__in=public_groups) | Q(group=anonymous_group) |
                            Q(group__in=group_list_all) |
                            Q(owner__username__iexact=str(request.user)))
                    except:
                        documents = documents.filter(
                            Q(group__isnull=True) | Q(group__in=groups) |
                            Q(group__in=group_list_all) | Q(group__in=public_groups) |
                            Q(owner__username__iexact=str(request.user)))
                else:
                    documents = documents.filter(Q(is_published=True) |
                                                 Q(owner__username__iexact=str(request.user)))

        if settings.RESOURCE_PUBLISHING:
            if not is_admin and not is_staff:
                if is_manager:
                    groups = request.user.groups.all()
                    group_list_all = request.user.group_list_all().values('group')
                    public_groups = GroupProfile.objects.exclude(access="private").values('group')
                    try:
                        anonymous_group = Group.objects.get(name='anonymous')
                        documents = documents.filter(
                            Q(group__isnull=True) | Q(group__in=groups) |
                            Q(group__in=public_groups) | Q(group=anonymous_group) |
                            Q(group__in=group_list_all) |
                            Q(owner__username__iexact=str(request.user)))
                    except:
                        documents = documents.filter(
                            Q(group__isnull=True) | Q(group__in=groups) |
                            Q(group__in=group_list_all) | Q(group__in=public_groups) |
                            Q(owner__username__iexact=str(request.user)))
                else:
                    documents = documents.filter(Q(is_published=True) |
                                                 Q(owner__username__iexact=str(request.user)))

        if settings.GROUP_PRIVATE_RESOURCES:
            public_groups = GroupProfile.objects.exclude(access="private").values('group')
            try:
                anonymous_group = Group.objects.get(name='anonymous')
            except:
                anonymous_group = None

            if is_admin:
                pass
            elif request.user:
                groups = request.user.groups.all()
                group_list_all = request.user.group_list_all().values('group')
                if anonymous_group:
                    documents = documents.filter(
                        Q(group__isnull=True) | Q(group__in=group_list_all) |
                        Q(group__in=groups) | Q(group__in=public_groups) |
                        Q(group=anonymous_group) |
                        Q(owner__username__iexact=str(request.user)))
                else:
                    documents = documents.filter(
                        Q(group__isnull=True) | Q(group__in=group_list_all) |
                        Q(group__in=groups) | Q(group__in=public_groups) |
                        Q(owner__username__iexact=str(request.user)))
            else:
                if anonymous_group:
                    documents = documents.filter(
                        Q(group__isnull=True) | Q(group__in=public_groups) | Q(group=anonymous_group))
                else:
                    documents = documents.filter(
                        Q(group__isnull=True) | Q(group__in=public_groups))

        if keywords_filter:
            treeqs = HierarchicalKeyword.objects.none()
            for keyword in keywords_filter:
                try:
                    kws = HierarchicalKeyword.objects.filter(name__iexact=keyword)
                    for kw in kws:
                        treeqs = treeqs | HierarchicalKeyword.get_tree(kw)
                except:
                    # Ignore keywords not actually used?
                    pass

            documents = documents.filter(Q(keywords__in=treeqs))

        if not settings.SKIP_PERMS_FILTER:
            documents = documents.filter(id__in=authorized)

        counts = documents.values('doc_type').annotate(count=Count('doc_type'))
        facets = dict([(count['doc_type'], count['count']) for count in counts])

        return facets

    else:

        layers = Layer.objects.filter(title__icontains=title_filter)

        if category_filter:
            layers = layers.filter(category__identifier__in=category_filter)

        if regions_filter:
            layers = layers.filter(regions__name__in=regions_filter)

        if owner_filter:
            layers = layers.filter(owner__username__in=owner_filter)

        if date_gte_filter:
            layers = layers.filter(date__gte=date_gte_filter)
        if date_lte_filter:
            layers = layers.filter(date__lte=date_lte_filter)
        if date_range_filter:
            layers = layers.filter(date__range=date_range_filter.split(','))

        if settings.ADMIN_MODERATE_UPLOADS:
            if not is_admin and not is_staff:
                if is_manager:
                    groups = request.user.groups.all()
                    group_list_all = request.user.group_list_all().values('group')
                    public_groups = GroupProfile.objects.exclude(access="private").values('group')
                    try:
                        anonymous_group = Group.objects.get(name='anonymous')
                        layers = layers.filter(
                            Q(group__isnull=True) | Q(group__in=groups) |
                            Q(group__in=group_list_all) | Q(group__in=public_groups) |
                            Q(group=anonymous_group) |
                            Q(owner__username__iexact=str(request.user)))
                    except:
                        layers = layers.filter(
                            Q(group__isnull=True) | Q(group__in=groups) |
                            Q(group__in=group_list_all) | Q(group__in=public_groups) |
                            Q(owner__username__iexact=str(request.user)))
                else:
                    layers = layers.filter(Q(is_published=True) |
                                           Q(owner__username__iexact=str(request.user)))

        if settings.RESOURCE_PUBLISHING:
            if not is_admin and not is_staff:
                if is_manager:
                    groups = request.user.groups.all()
                    group_list_all = request.user.group_list_all().values('group')
                    public_groups = GroupProfile.objects.exclude(access="private").values('group')
                    try:
                        anonymous_group = Group.objects.get(name='anonymous')
                        layers = layers.filter(
                            Q(group__isnull=True) | Q(group__in=groups) |
                            Q(group__in=group_list_all) | Q(group__in=public_groups) |
                            Q(group=anonymous_group) |
                            Q(owner__username__iexact=str(request.user)))
                    except:
                        layers = layers.filter(
                            Q(group__isnull=True) | Q(group__in=groups) |
                            Q(group__in=group_list_all) | Q(group__in=public_groups) |
                            Q(owner__username__iexact=str(request.user)))
                else:
                    layers = layers.filter(Q(is_published=True) |
                                           Q(owner__username__iexact=str(request.user)))

        if settings.GROUP_PRIVATE_RESOURCES:
            public_groups = GroupProfile.objects.exclude(access="private").values('group')
            try:
                anonymous_group = Group.objects.get(name='anonymous')
            except:
                anonymous_group = None

            if is_admin:
                pass
            elif request.user:
                groups = request.user.groups.all()
                group_list_all = request.user.group_list_all().values('group')
                if anonymous_group:
                    layers = layers.filter(
                        Q(group__isnull=True) | Q(group__in=groups) |
                        Q(group__in=group_list_all) | Q(group__in=public_groups) |
                        Q(group=anonymous_group) | Q(owner__username__iexact=str(request.user)))
                else:
                    layers = layers.filter(
                        Q(group__isnull=True) | Q(group__in=group_list_all) |
                        Q(group__in=groups) | Q(group__in=public_groups) |
                        Q(owner__username__iexact=str(request.user)))
            else:
                if anonymous_group:
                    layers = layers.filter(
                        Q(group__isnull=True) | Q(group__in=public_groups) | Q(group=anonymous_group))
                else:
                    layers = layers.filter(
                        Q(group__isnull=True) | Q(group__in=public_groups))

        if extent_filter:
            bbox = extent_filter.split(
                ',')  # TODO: Why is this different when done through haystack?
            bbox = map(str, bbox)  # 2.6 compat - float to decimal conversion
            intersects = ~(Q(bbox_x0__gt=bbox[2]) | Q(bbox_x1__lt=bbox[0]) |
                           Q(bbox_y0__gt=bbox[3]) | Q(bbox_y1__lt=bbox[1]))

            layers = layers.filter(intersects)

        if keywords_filter:
            treeqs = HierarchicalKeyword.objects.none()
            for keyword in keywords_filter:
                try:
                    kws = HierarchicalKeyword.objects.filter(name__iexact=keyword)
                    for kw in kws:
                        treeqs = treeqs | HierarchicalKeyword.get_tree(kw)
                except:
                    # Ignore keywords not actually used?
                    pass

            layers = layers.filter(Q(keywords__in=treeqs))

        if not settings.SKIP_PERMS_FILTER:
            layers = layers.filter(id__in=authorized)

        counts = layers.values('storeType').annotate(count=Count('storeType'))
        count_dict = dict([(count['storeType'], count['count']) for count in counts])

        facets = {
            'raster': count_dict.get('coverageStore', 0),
            'vector': count_dict.get('dataStore', 0),
            'remote': count_dict.get('remoteStore', 0),
            'wms': count_dict.get('wmsStore', 0),
        }

        # Break early if only_layers is set.
        if facet_type == 'layers':
            return facets

        maps = Map.objects.filter(title__icontains=title_filter)
        documents = Document.objects.filter(title__icontains=title_filter)

        if category_filter:
            maps = maps.filter(category__identifier__in=category_filter)
            documents = documents.filter(category__identifier__in=category_filter)

        if regions_filter:
            maps = maps.filter(regions__name__in=regions_filter)
            documents = documents.filter(regions__name__in=regions_filter)

        if owner_filter:
            maps = maps.filter(owner__username__in=owner_filter)
            documents = documents.filter(owner__username__in=owner_filter)

        if date_gte_filter:
            maps = maps.filter(date__gte=date_gte_filter)
            documents = documents.filter(date__gte=date_gte_filter)
        if date_lte_filter:
            maps = maps.filter(date__lte=date_lte_filter)
            documents = documents.filter(date__lte=date_lte_filter)
        if date_range_filter:
            maps = maps.filter(date__range=date_range_filter.split(','))
            documents = documents.filter(date__range=date_range_filter.split(','))

        if settings.ADMIN_MODERATE_UPLOADS:
            if not is_admin and not is_staff:
                if is_manager:
                    groups = request.user.groups.all()
                    group_list_all = request.user.group_list_all().values('group')
                    public_groups = GroupProfile.objects.exclude(access="private").values('group')
                    try:
                        anonymous_group = Group.objects.get(name='anonymous')
                        maps = maps.filter(
                            Q(group__isnull=True) | Q(group__in=groups) |
                            Q(group__in=group_list_all) | Q(group__in=public_groups) |
                            Q(group=anonymous_group) |
                            Q(owner__username__iexact=str(request.user)))
                        documents = documents.filter(
                            Q(group__isnull=True) | Q(group__in=groups) |
                            Q(group__in=group_list_all) | Q(group__in=public_groups) |
                            Q(group=anonymous_group) |
                            Q(owner__username__iexact=str(request.user)))
                    except:
                        maps = maps.filter(
                            Q(group__isnull=True) | Q(group__in=groups) |
                            Q(group__in=group_list_all) | Q(group__in=public_groups) |
                            Q(owner__username__iexact=str(request.user)))
                        documents = documents.filter(
                            Q(group__isnull=True) | Q(group__in=groups) |
                            Q(group__in=group_list_all) | Q(group__in=public_groups) |
                            Q(owner__username__iexact=str(request.user)))
                else:
                    maps = maps.filter(Q(is_published=True) |
                                       Q(owner__username__iexact=str(request.user)))
                    documents = documents.filter(Q(is_published=True) |
                                                 Q(owner__username__iexact=str(request.user)))

        if settings.RESOURCE_PUBLISHING:
            if not is_admin and not is_staff:
                if is_manager:
                    groups = request.user.groups.all()
                    group_list_all = request.user.group_list_all().values('group')
                    public_groups = GroupProfile.objects.exclude(access="private").values('group')
                    try:
                        anonymous_group = Group.objects.get(name='anonymous')
                        maps = maps.filter(
                            Q(group__isnull=True) | Q(group__in=groups) |
                            Q(group__in=group_list_all) | Q(group__in=public_groups) |
                            Q(group=anonymous_group) |
                            Q(owner__username__iexact=str(request.user)))
                        documents = documents.filter(
                            Q(group__isnull=True) | Q(group__in=groups) |
                            Q(group__in=group_list_all) | Q(group__in=public_groups) |
                            Q(group=anonymous_group) |
                            Q(owner__username__iexact=str(request.user)))
                    except:
                        maps = maps.filter(
                            Q(group__isnull=True) | Q(group__in=group_list_all) |
                            Q(group__in=groups) | Q(group__in=public_groups) |
                            Q(owner__username__iexact=str(request.user)))
                        documents = documents.filter(
                            Q(group__isnull=True) | Q(group__in=group_list_all) |
                            Q(group__in=groups) | Q(group__in=public_groups) |
                            Q(owner__username__iexact=str(request.user)))
                else:
                    maps = maps.filter(Q(is_published=True) | Q(owner__username__iexact=str(request.user)))
                    documents = documents.filter(Q(is_published=True) | Q(owner__username__iexact=str(request.user)))

        if settings.GROUP_PRIVATE_RESOURCES:
            public_groups = GroupProfile.objects.exclude(access="private").values('group')
            try:
                anonymous_group = Group.objects.get(name='anonymous')
            except:
                anonymous_group = None

            if is_admin:
                pass
            elif request.user:
                groups = request.user.groups.all()
                group_list_all = request.user.group_list_all().values('group')
                if anonymous_group:
                    maps = maps.filter(
                        Q(group__isnull=True) | Q(group__in=group_list_all) |
                        Q(group__in=groups) | Q(group=anonymous_group) |
                        Q(owner__username__iexact=str(request.user)))
                    documents = documents.filter(
                        Q(group__isnull=True) | Q(group__in=group_list_all) |
                        Q(group__in=groups) | Q(group=anonymous_group) |
                        Q(owner__username__iexact=str(request.user)))
                else:
                    maps = maps.filter(
                        Q(group__isnull=True) | Q(group__in=group_list_all) |
                        Q(group__in=groups) |
                        Q(owner__username__iexact=str(request.user)))
                    documents = documents.filter(
                        Q(group__isnull=True) | Q(group__in=group_list_all) |
                        Q(group__in=groups) |
                        Q(owner__username__iexact=str(request.user)))
            else:
                if anonymous_group:
                    maps = maps.filter(Q(group__isnull=True) | Q(group=anonymous_group))
                    documents = documents.filter(Q(group__isnull=True) | Q(group=anonymous_group))
                else:
                    maps = maps.filter(Q(group__isnull=True))
                    documents = documents.filter(Q(group__isnull=True))

        if extent_filter:
            bbox = extent_filter.split(
                ',')  # TODO: Why is this different when done through haystack?
            bbox = map(str, bbox)  # 2.6 compat - float to decimal conversion
            intersects = ~(Q(bbox_x0__gt=bbox[2]) | Q(bbox_x1__lt=bbox[0]) |
                           Q(bbox_y0__gt=bbox[3]) | Q(bbox_y1__lt=bbox[1]))

            maps = maps.filter(intersects)
            documents = documents.filter(intersects)

        if keywords_filter:
            treeqs = HierarchicalKeyword.objects.none()
            for keyword in keywords_filter:
                try:
                    kws = HierarchicalKeyword.objects.filter(name__iexact=keyword)
                    for kw in kws:
                        treeqs = treeqs | HierarchicalKeyword.get_tree(kw)
                except:
                    # Ignore keywords not actually used?
                    pass

            maps = maps.filter(Q(keywords__in=treeqs))
            documents = documents.filter(Q(keywords__in=treeqs))

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
                facets['vector'] + facets['remote'] + facets['wms']

    return facets


@register.assignment_tag(takes_context=True)
def get_current_path(context):
    request = context['request']
    return request.get_full_path()


@register.assignment_tag(takes_context=True)
def get_context_resourcetype(context):
    c_path = get_current_path(context)
    resource_types = ['layers', 'maps', 'documents', 'search', 'people',
                      'groups']
    for resource_type in resource_types:
        if "/{0}/".format(resource_type) in c_path:
            return resource_type
    return 'error'


@register.simple_tag(takes_context=True)
def fullurl(context, url):
    if not url:
        return ''
    r = context['request']
    return r.build_absolute_uri(url)
