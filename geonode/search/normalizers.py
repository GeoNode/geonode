#########################################################################
#
# Copyright (C) 2012 OpenPlans
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

from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.template import defaultfilters

from geonode.maps.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.search import extension

from agon_ratings.categories import RATING_CATEGORY_LOOKUP
from agon_ratings.models import OverallRating

from avatar.util import get_default_avatar_url

_default_avatar_url = get_default_avatar_url()

def _bbox(obj):
    idx = None
    # the one-to-one reverse relationship requires special handling if null :(
    # maybe one day: https://code.djangoproject.com/ticket/10227
    try:
        idx = obj.spatial_temporal_index
    except ObjectDoesNotExist:
        pass
    except AttributeError:
        pass
    # unknown extent, just give something that works
    extent = idx.extent.extent if idx else map(str,(obj.bbox_x0, obj.bbox_y0, obj.bbox_x1, obj.bbox_y1))
    return dict(minx=extent[0], miny=extent[1], maxx=extent[2], maxy=extent[3])


def _get_ratings(model):
    '''cached, bulk access for a given models rating'''
    key = 'overall_rating_%s' % model.__name__
    results = cache.get(key)
    if not results:
        # this is some hacky stuff related to rankings
        choice = model.__name__.lower()
        category = RATING_CATEGORY_LOOKUP.get(
            "%s.%s-%s" % (model._meta.app_label, model._meta.object_name, choice)
        )
        try:
            ct = ContentType.objects.get_for_model(model)
            ratings = OverallRating.objects.filter(
                content_type = ct,
                category = category
            )
            results = dict([ (r.object_id, r.rating) or 0 for r in ratings])
            cache.set(key, results)
        except OverallRating.DoesNotExist:
            return {}
    return results


def _annotate(normalizers):
    '''annotate normalizers with any attributes that are better fetched in bulk'''
    if not normalizers: return
    model = type(normalizers[0].o)
    ratings = _get_ratings(model)
    for n in normalizers:
        n.rating = float(ratings.get(n.o.id, 0))


def apply_normalizers(results):
    '''build the appropriate normalizers for the query set(s) and annotate'''
    normalized = []
    mapping = [
        ('maps', MapNormalizer),
        ('layers', LayerNormalizer),
        ('documents', DocumentNormalizer),
        ('owners', OwnerNormalizer),
    ]
    for k,n in mapping:
        r = results.get(k, None)
        if not r: continue
        normalizers = map(n, r)
        _annotate(normalizers)
        extension.process_results(normalizers)
        normalized.extend(normalizers)
    return normalized


class Normalizer:
    '''Base class to allow lazy normalization of Map and Layer attributes.

    The fields we support sorting on are rank, title, last_modified.
    Instead of storing these (to keep pickle query size small), expose via methods.
    '''
    def __init__(self,o,data = None):
        self.o = o
        self.data = data
        self.dict = None
    def rank(self):
        return self.rating
    def title(self):
        return self.o.title
    def last_modified(self):
        raise Exception('abstract')
    def relevance(self):
        return getattr(self.o, 'relevance', 0)
    def as_dict(self, exclude):
        if self.dict is None:
            if self.o._deferred:
                self.o = getattr(type(self.o),'objects').get(pk = self.o.pk)
            self.dict = self.populate(self.data or {}, exclude)
            self.dict['iid'] = self.iid
            self.dict['relevance'] = getattr(self.o, 'relevance', 0)
            if hasattr(self,'views'):
                self.dict['views'] = self.views
            self.dict['rating'] = self.rating
        if exclude:
            for e in exclude:
                if e in self.dict: self.dict.pop(e)
        return self.dict


class MapNormalizer(Normalizer):
    def last_modified(self):
        return self.o.last_modified
    def populate(self, doc, exclude):
        mapobj = self.o
        # resolve any local layers and their keywords
        local_kw = [ l.keyword_list() for l in mapobj.local_layers if l.keywords]
        keywords = local_kw and list(set( reduce(lambda a,b: a+b, local_kw))) or []
        doc['id'] = mapobj.id
        doc['title'] = mapobj.title
        doc['abstract'] = defaultfilters.linebreaks(mapobj.abstract)
        doc['category'] = mapobj.category.slug if mapobj.category else 'location'
        doc['detail'] = reverse('map_detail', args=(mapobj.id,))
        doc['owner'] = mapobj.owner.username
        doc['owner_detail'] = mapobj.owner.get_absolute_url()
        doc['last_modified'] = extension.date_fmt(mapobj.last_modified)
        doc['_type'] = 'map'
        doc['_display_type'] = extension.MAP_DISPLAY
#        doc['thumb'] = map.get_thumbnail_url()
        doc['keywords'] = keywords
        if 'bbox' not in exclude:
            doc['bbox'] = _bbox(mapobj)
        return doc


class LayerNormalizer(Normalizer):
    def last_modified(self):
        return self.o.date
    def populate(self, doc, exclude):
        layer = self.o
        doc['owner'] = layer.owner.username if layer.owner else None
#        doc['thumb'] = layer.get_thumbnail_url()
        doc['last_modified'] = extension.date_fmt(layer.date)
        doc['id'] = layer.id
        doc['_type'] = 'layer'
#        doc['owsUrl'] = layer.get_virtual_wms_url()
        doc['category'] = layer.category.slug if layer.category else 'location'
        doc['name'] = layer.typename
        doc['abstract'] = defaultfilters.linebreaks(layer.abstract)
        doc['storeType'] = layer.storeType
        doc['_display_type'] = extension.LAYER_DISPLAY
        if 'bbox' not in exclude:
            doc['bbox'] = _bbox(layer)
        doc['keywords'] = layer.keyword_list()
        doc['title'] = layer.title
        doc['detail'] = layer.get_absolute_url()
        if 'download_links' not in exclude:
            links = {}
            for l in layer.link_set.all():
                link = {}
                link['name'] = l.name
                link['extension'] = l.extension
                link['url'] = l.url
                link['mime'] = l.mime
                link['type'] = l.link_type
                links[l.extension] = link
            for s in layer.styles.all():
                link = {}
                link['name'] = s.name
                link['url'] = s.sld_url
                link['type'] = 'style'
                links['sld'] = link
            doc['links'] = links

        owner = layer.owner
        if owner:
            doc['owner_detail'] = layer.owner.get_absolute_url()
        return doc

class DocumentNormalizer(Normalizer):
    def last_modified(self):
        return self.o.date
    def populate(self, doc, exclude):
        document = self.o
        doc['id'] = document.id
        doc['title'] = document.title
        doc['abstract'] = defaultfilters.linebreaks(document.abstract)
        doc['category'] = document.category.slug if document.category else 'location'
        doc['detail'] = reverse('document_detail', args=(document.id,))
        doc['owner'] = document.owner.username
        doc['owner_detail'] = document.owner.get_absolute_url()
        doc['last_modified'] = extension.date_fmt(document.date)
        doc['_type'] = 'document'
        doc['_display_type'] = extension.DOCUMENT_DISPLAY
#        doc['thumb'] = map.get_thumbnail_url()
        doc['keywords'] = document.keyword_list()
        if 'bbox' not in exclude:
            doc['bbox'] = _bbox(document)
        return doc

class OwnerNormalizer(Normalizer):
    def title(self):
        return self.o.user.get_full_name() or self.o.user.username
    def last_modified(self):
        try:
            return self.o.user.date_joined
        except ObjectDoesNotExist:
            return None
    def populate(self, doc, exclude):
        contact = self.o
        user = contact.user
        try:
            doc['thumb'] = user.avatar_set.all()[0].avatar_url(80)
        except IndexError:
            doc['thumb'] = _default_avatar_url
        doc['id'] = user.username
        doc['title'] = user.get_full_name() or user.username
        doc['organization'] = contact.organization
        doc['abstract'] = contact.profile
        modified = self.last_modified()
        doc['last_modified'] = extension.date_fmt(modified) if modified else ''
        doc['detail'] = contact.get_absolute_url()
        doc['layer_cnt'] = Layer.objects.filter(owner = user).count()
        doc['map_cnt'] = Map.objects.filter(owner = user).count()
        doc['doc_cnt'] = Document.objects.filter(owner = user).count()
        doc['_type'] = 'owner'
        doc['_display_type'] = extension.USER_DISPLAY
        return doc
