from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.template import defaultfilters

from geonode.maps.models import Layer
from geonode.maps.models import Map
from geonode.silage import extension

import avatar

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
    extent = idx.extent.extent if idx else (-180,-90,180,90)
    return dict(minx=extent[0], miny=extent[1], maxx=extent[2], maxy=extent[3])


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
        return (self.rating + 1) * (self.views + 1)
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
            self.dict['rating'] = self.rating
            self.dict['relevance'] = getattr(self.o, 'relevance', 0)
            if hasattr(self,'views'):
                self.dict['views'] = self.views
        if exclude:
            for e in exclude:
                if e in self.dict: self.dict.pop(e)
        return self.dict
    
    
class MapNormalizer(Normalizer):
    def last_modified(self):
        return self.o.last_modified
    def populate(self, doc, exclude):
        map = self.o
        # resolve any local layers and their keywords
        # @todo this makes this search awful slow and these should be lazily evaluated
        local_kw = [ l.keyword_list() for l in map.local_layers if l.keywords]
        keywords = local_kw and list(set( reduce(lambda a,b: a+b, local_kw))) or []
        doc['id'] = map.id
        doc['title'] = map.title
        doc['abstract'] = defaultfilters.linebreaks(map.abstract)
        doc['topic'] = '', # @todo
        doc['detail'] = reverse('geonode.maps.views.map_controller', args=(map.id,))
        doc['owner'] = map.owner.username
        doc['owner_detail'] = reverse('about_storyteller', args=(map.owner.username,))
        doc['last_modified'] = extension.date_fmt(map.last_modified)
        doc['_type'] = 'map'
        doc['_display_type'] = extension.MAP_DISPLAY
        doc['thumb'] = map.get_thumbnail_url()
        doc['keywords'] = keywords
        if 'bbox' not in exclude:
            doc['bbox'] = _bbox(map)
        return doc


class LayerNormalizer(Normalizer):
    def last_modified(self):
        return self.o.date
    def populate(self, doc, exclude):
        layer = self.o
        doc['owner'] = layer.owner.username
        doc['thumb'] = layer.get_thumbnail_url()
        doc['last_modified'] = extension.date_fmt(layer.date)
        doc['id'] = layer.id
        doc['_type'] = 'layer'
        doc['owsUrl'] = layer.get_virtual_wms_url()
        doc['topic'] = layer.topic_category
        doc['name'] = layer.typename
        doc['abstract'] = defaultfilters.linebreaks(layer.abstract)
        doc['storeType'] = layer.storeType
        doc['_display_type'] = extension.LAYER_DISPLAY
        if 'bbox' not in exclude:
            doc['bbox'] = _bbox(layer)
        doc['keywords'] = layer.keyword_list()
        doc['title'] = layer.title
        doc['detail'] = layer.get_absolute_url()
        #if 'download_links' not in exclude:
        #    links = layer.download_links()
        #    for i,e in enumerate(links):
        #        links[i] = [ unicode(l) for l in e]
        #    doc['download_links'] = links
        owner = layer.owner
        if owner:
            doc['owner_detail'] = reverse('about_storyteller', args=(layer.owner.username,))
        return doc


class OwnerNormalizer(Normalizer):
    def title(self):
        return self.o.user.username
    def last_modified(self):
        return self.o.user.date_joined
    def populate(self, doc, exclude):
        contact = self.o
        user = contact.user
        try:
            doc['thumb'] = user.avatar_set.all()[0].avatar_url(80)
        except IndexError:
            doc['thumb'] = avatar.AVATAR_DEFAULT_URL
        doc['id'] = user.username
        doc['title'] = user.get_full_name() or user.username
        doc['organization'] = contact.organization
        doc['abstract'] = contact.blurb
        doc['last_modified'] = extension.date_fmt(self.last_modified())
        doc['detail'] = reverse('about_storyteller', args=(user.username,))
        doc['layer_cnt'] = Layer.objects.filter(owner = user).count()
        doc['map_cnt'] = Map.objects.filter(owner = user).count()
        doc['_type'] = 'owner'
        doc['_display_type'] = extension.USER_DISPLAY
        return doc