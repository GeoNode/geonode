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

from enum import Enum
import logging

from django import template
from django.db.models import Q
from django.conf import settings
from django.db.models import Count
from django.utils.translation import ugettext
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from pinax.ratings.models import Rating
from guardian.shortcuts import get_objects_for_user

from geonode.base.models import ExtraMetadata, ResourceBase
from geonode.base.bbox_utils import filter_bbox
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.groups.models import GroupProfile
from geonode.base.models import (
    HierarchicalKeyword, Menu, MenuItem
)
from geonode.security.utils import get_visible_resources
from collections import OrderedDict, Counter

from geonode.utils import get_geoapps_models

logger = logging.getLogger(__name__)

register = template.Library()

FACETS = {
    'raster': _('Raster Layer'),
    'vector': _('Vector Layer'),
    'vector_time': _('Vector Temporal Serie'),
    'remote': _('Remote Layer'),
    'wms': _('WMS Cascade Layer')
}


class FACET_TO_RESOURCE_TYPE(Enum):
    layers = 'layer'
    maps = 'map'
    documents = 'document'
    geoapps = 'geoapp'


@register.filter(name='template_trans')
def template_trans(text):
    try:
        return ugettext(text)
    except Exception:
        return text


@register.simple_tag
def num_ratings(obj):
    ct = ContentType.objects.get_for_model(obj)
    return len(Rating.objects.filter(object_id=obj.pk, content_type=ct))


@register.simple_tag(takes_context=True)
def facets(context):
    request = context['request']
    title_filter = request.GET.get('title__icontains', '')
    abstract_filter = request.GET.get('abstract__icontains', '')
    purpose_filter = request.GET.get('purpose__icontains', '')
    extent_filter = request.GET.get('extent', None)
    keywords_filter = request.GET.getlist('keywords__slug__in', None)
    category_filter = request.GET.getlist('category__identifier__in', None)
    regions_filter = request.GET.getlist('regions__name__in', None)
    owner_filter = request.GET.getlist('owner__username__in', None)
    date_gte_filter = request.GET.get('date__gte', None)
    date_lte_filter = request.GET.get('date__lte', None)
    date_range_filter = request.GET.get('date__range', None)

    facet_type = context.get('facet_type', 'all')
    facet_geoapp = {}
    if not settings.SKIP_PERMS_FILTER:
        authorized = []
        try:
            authorized = get_objects_for_user(
                request.user, 'base.view_resourcebase').values('id')
        except Exception:
            pass

    if facet_type == 'geoapps':
        return _facets_geoapps(
            request,
            title_filter,
            abstract_filter,
            purpose_filter,
            category_filter,
            regions_filter,
            owner_filter,
            date_gte_filter,
            date_lte_filter,
            date_range_filter,
            extent_filter,
            keywords_filter,
            authorized
        )
    elif facet_type == 'documents':
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

        documents = get_visible_resources(
            documents,
            request.user if request else None,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)

        if keywords_filter:
            treeqs = HierarchicalKeyword.objects.none()
            for keyword in keywords_filter:
                try:
                    kws = HierarchicalKeyword.objects.filter(name__iexact=keyword)
                    for kw in kws:
                        treeqs = treeqs | HierarchicalKeyword.get_tree(kw)
                except Exception:
                    # Ignore keywords not actually used?
                    pass

            documents = documents.filter(Q(keywords__in=treeqs))

        if not settings.SKIP_PERMS_FILTER:
            documents = documents.filter(id__in=authorized)

        counts = documents.values('doc_type').annotate(count=Count('doc_type'))
        facets = {count['doc_type']: count['count'] for count in counts}

        return facets
    else:
        layers = Layer.objects.filter(
            Q(title__icontains=title_filter) |
            Q(abstract__icontains=abstract_filter) |
            Q(purpose__icontains=purpose_filter)
        )
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

        layers = get_visible_resources(
            layers,
            request.user if request else None,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)

        if extent_filter:
            layers = filter_bbox(layers, extent_filter)

        if keywords_filter:
            treeqs = HierarchicalKeyword.objects.none()
            for keyword in keywords_filter:
                try:
                    kws = HierarchicalKeyword.objects.filter(name__iexact=keyword)
                    for kw in kws:
                        treeqs = treeqs | HierarchicalKeyword.get_tree(kw)
                except Exception:
                    # Ignore keywords not actually used?
                    pass

            layers = layers.filter(Q(keywords__in=treeqs))

        if not settings.SKIP_PERMS_FILTER:
            layers = layers.filter(id__in=authorized)

        counts = layers.values('storeType').annotate(count=Count('storeType'))

        counts_array = []
        try:
            for count in counts:
                counts_array.append((count['storeType'], count['count']))
        except Exception:
            pass

        count_dict = dict(counts_array)

        vector_time_series = layers.exclude(has_time=False).filter(storeType='dataStore'). \
            values('storeType').annotate(count=Count('storeType'))

        if vector_time_series:
            count_dict['vectorTimeSeries'] = vector_time_series[0]['count']

        facets = {
            'raster': count_dict.get('coverageStore', 0),
            'vector': count_dict.get('dataStore', 0),
            'vector_time': count_dict.get('vectorTimeSeries', 0),
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

        maps = get_visible_resources(
            maps,
            request.user if request else None,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)
        documents = get_visible_resources(
            documents,
            request.user if request else None,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)

        if extent_filter:
            documents = filter_bbox(documents, extent_filter)

        if keywords_filter:
            treeqs = HierarchicalKeyword.objects.none()
            for keyword in keywords_filter:
                try:
                    kws = HierarchicalKeyword.objects.filter(name__iexact=keyword)
                    for kw in kws:
                        treeqs = treeqs | HierarchicalKeyword.get_tree(kw)
                except Exception:
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

            facets['layer'] = facets['raster'] + facets['vector'] + facets['remote'] + facets['wms']

        if settings.GEONODE_APPS_ENABLE:
            facet_geoapp = _facets_geoapps(
                request,
                title_filter,
                abstract_filter,
                purpose_filter,
                category_filter,
                regions_filter,
                owner_filter,
                date_gte_filter,
                date_lte_filter,
                date_range_filter,
                extent_filter,
                keywords_filter,
                authorized
            )

        facets = {
            **facets,
            **facet_geoapp
        }
    return facets


def _facets_geoapps(
        request,
        title_filter,
        abstract_filter,
        purpose_filter,
        category_filter,
        regions_filter,
        owner_filter,
        date_gte_filter,
        date_lte_filter,
        date_range_filter,
        extent_filter,
        keywords_filter,
        authorized):
    result = {}
    from django.apps import apps
    for label, app in apps.app_configs.items():
        if hasattr(app, 'type') and app.type == 'GEONODE_APP' and hasattr(app, 'default_model'):
            geoapps = get_visible_resources(
                apps.get_model(label, app.default_model).objects.all(),
                request.user if request else None,
                admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
                unpublished_not_visible=settings.RESOURCE_PUBLISHING,
                private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)
            geoapp_filters = {}
            if category_filter:
                geoapp_filters['category__identifier__in'] = category_filter
            if regions_filter:
                geoapp_filters['regions__name__in'] = regions_filter
            if owner_filter:
                geoapp_filters['owner__username__in'] = owner_filter
            if date_gte_filter:
                geoapp_filters['date__gte'] = date_gte_filter
            if date_lte_filter:
                geoapp_filters['date__lte'] = date_lte_filter
            if date_range_filter:
                geoapp_filters['date__range'] = date_range_filter.split(',')

            geoapps = geoapps.filter(**geoapp_filters)

            try:
                geoapps = geoapps.filter(
                    Q(title__icontains=title_filter) |
                    Q(abstract__icontains=abstract_filter) |
                    Q(purpose__icontains=purpose_filter)
                )
            except Exception as e:
                logger.exception(e)

            if extent_filter:
                geoapps = filter_bbox(geoapps, extent_filter)

            if keywords_filter:
                treeqs = HierarchicalKeyword.objects.none()
                for keyword in keywords_filter:
                    try:
                        kws = HierarchicalKeyword.objects.filter(name__iexact=keyword)
                        for kw in kws:
                            treeqs = treeqs | HierarchicalKeyword.get_tree(kw)
                    except Exception:
                        # Ignore keywords not actually used?
                        pass

                geoapps = geoapps.filter(Q(keywords__in=treeqs))

            if not settings.SKIP_PERMS_FILTER:
                geoapps = geoapps.filter(id__in=authorized)

            result[app.default_model] = geoapps.count()
    return result


@register.filter(is_safe=True)
def get_facet_title(value):
    """Converts a facet_type into a human readable string"""
    if value in FACETS.keys():
        return FACETS[value]
    return value


@register.simple_tag(takes_context=True)
def get_current_path(context):
    request = context['request']
    return request.get_full_path()


@register.simple_tag(takes_context=True)
def get_context_resourcetype(context):
    c_path = get_current_path(context)
    resource_types = ['layers', 'maps', 'geoapps', 'documents', 'search', 'people',
                      'groups/categories', 'groups']
    for resource_type in resource_types:
        if f"/{resource_type}/" in c_path:
            return resource_type
    return 'error'


@register.simple_tag(takes_context=True)
def fullurl(context, url):
    if not url:
        return ''
    r = context['request']
    return r.build_absolute_uri(url)


@register.simple_tag
def get_menu(placeholder_name):
    menus = {
        m: MenuItem.objects.filter(menu=m).order_by('order')
        for m in Menu.objects.filter(placeholder__name=placeholder_name)
    }
    return OrderedDict(menus.items())


@register.inclusion_tag(filename='base/menu.html')
def render_nav_menu(placeholder_name):
    menus = {}
    try:
        menus = {
            m: MenuItem.objects.filter(menu=m).order_by('order')
            for m in Menu.objects.filter(placeholder__name=placeholder_name)
        }
    except Exception:
        pass

    return {'menus': OrderedDict(menus.items())}


@register.inclusion_tag(filename='base/iso_categories.html')
def get_visibile_resources(user):
    categories = get_objects_for_user(user, 'view_resourcebase', klass=ResourceBase, any_perm=False)\
        .filter(category__isnull=False).values('category__gn_description',
                                               'category__fa_class', 'category__description', 'category__identifier')\
        .annotate(count=Count('category'))

    return {
        'iso_formats': categories
    }


@register.simple_tag
def display_edit_request_button(resource, user, perms):
    def _has_owner_his_permissions():
        _owner_perms = set(
            resource.BASE_PERMISSIONS.get('owner') +
            resource.BASE_PERMISSIONS.get('read') +
            resource.BASE_PERMISSIONS.get('write')
        )

        if resource.polymorphic_ctype.model in ['layer', 'document']:
            '''
            The download resource permission should be available only
            if the resource is a layer or Documents. You cant downlod maps
            '''
            _owner_perms = _owner_perms.union(set(resource.BASE_PERMISSIONS.get('download')))

        _owner_set = _owner_perms.difference(set(perms))
        return _owner_set == set() or \
            _owner_set == {'change_resourcebase_permissions', 'publish_resourcebase'}

    if not _has_owner_his_permissions() and \
            (user.is_superuser or resource.owner.pk == user.pk):
        return True
    return False


@register.simple_tag
def display_change_perms_button(resource, user, perms):
    try:
        from geonode.geoserver.helpers import ogc_server_settings
    except Exception:
        return False
    if not getattr(ogc_server_settings, 'GEONODE_SECURITY_ENABLED', False):
        return False
    elif user.is_superuser or 'change_resourcebase_permissions' in set(perms):
        return True
    else:
        return not getattr(settings, 'ADMIN_MODERATE_UPLOADS', False)


@register.simple_tag
def get_layer_count_by_services(service_id, user):
    return get_visible_resources(
        queryset=Layer.objects.filter(remote_service=service_id),
        user=user
    ).count()


@register.simple_tag(takes_context=True)
def dynamic_metadata_filters(context):

    facet_type = context.get('facet_type', 'all')

    metadata_available = ExtraMetadata.objects.all()

    if facet_type != 'all':
        resource_type = [getattr(FACET_TO_RESOURCE_TYPE, facet_type).value]
        if 'geoapp' in resource_type:
            resource_type = [''.join(list(x.models)) for x in get_geoapps_models()]
        metadata_available = metadata_available\
            .filter(resource__polymorphic_ctype__model__in=resource_type)

    if not metadata_available.exists():
        return []

    categories = metadata_available.values_list('metadata__filter_header', flat=True).distinct()

    output = {}

    for _cat in categories:
        output[_cat] = _get_filter_by_category(_cat, metadata_available)

    return output


def _get_filter_by_category(category, metadata_available):
    metadata_for_category = metadata_available\
        .filter(metadata__filter_header=category)

    counters = Counter(metadata_for_category.values_list('metadata__field_name', 'metadata__field_value'))
    out = []
    for _el in metadata_for_category.distinct("metadata__field_name", "metadata__field_value"):
        cnt = counters.get((_el.metadata['field_name'], _el.metadata['field_value']), 0)
        out.append({**{"id": _el.id, "count": cnt}, **_el.metadata})
    return out
