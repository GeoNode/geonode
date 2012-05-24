import json

from django.conf import settings
from django.core.urlresolvers import reverse

from haystack import indexes

from geonode.maps.models import Layer, Map, Thumbnail, Contact
from django.contrib.gis.geos import GEOSGeometry

class LayerIndex(indexes.RealTimeSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    iid = indexes.IntegerField(model_attr='id')
    type = indexes.CharField(faceted=True)
    subtype = indexes.CharField(faceted=True)
    name = indexes.CharField(model_attr="title")
    description = indexes.CharField(model_attr="abstract")
    owner = indexes.CharField(model_attr="owner", faceted=True)
    created = indexes.DateTimeField(model_attr="date")
    modified = indexes.DateTimeField(model_attr="date")
    category = indexes.CharField(model_attr="topic_category", faceted=True)
    keywords = indexes.CharField(model_attr="keywords", faceted=True)
    language = indexes.CharField(model_attr="language", faceted=True)
    detail_url = indexes.CharField(model_attr="get_absolute_url")
    bbox_left = indexes.FloatField(model_attr='bbox_left')
    bbox_right = indexes.FloatField(model_attr='bbox_right')
    bbox_top = indexes.FloatField(model_attr='bbox_top')
    bbox_bottom = indexes.FloatField(model_attr='bbox_bottom')

    json = indexes.CharField(indexed=False)

    def get_model(self):
        return Layer

    def prepare_type(self, obj):
        return "layer"

    def prepare_subtype(self, obj):
        if obj.storeType == "dataStore":
            return "vector"
        elif obj.storeType == "coverageStore":
            return "raster"
            
    def prepare_download_links(self,obj):
        prepped = [(ext,name.encode(),extra) for ext,name,extra in obj]
        return prepped
		
    def prepare_json(self, obj):
        bbox = obj.resource.latlon_bbox
        poc_profile = Contact.objects.get(user=obj.poc.user)
		
        data = {
            "id": obj.id,
            "uuid": obj.uuid,
            "_type": self.prepare_type(obj),
            "_display_type": obj.display_type,
            "subtype": self.prepare_subtype(obj),
            "title": obj.title,
            "name": obj.typename,
            "description": obj.abstract,
            "owner": obj.metadata_author.name,
            "owner_detail": obj.owner.get_absolute_url(),
            "last_modified": obj.date.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "category": obj.topic_category,
            "keywords": [keyword.name for keyword in obj.keywords.all()] if obj.keywords else [],
            "thumb": Thumbnail.objects.get_thumbnail(obj),
            "detail_url": obj.get_absolute_url(),  # @@@ Use Sites Framework?
            "download_links": self.prepare_download_links(obj.download_links()),
            "metadata_links": obj.metadata_links,
            "bbox": {
                "minx": bbox[0],
                "miny": bbox[2],
                "maxx": bbox[1],
                "maxy": bbox[3],
            },
            "attribution": {
                "title": poc_profile.name,
                "href": poc_profile.get_absolute_url(),
            },
        }

        return json.dumps(data)


class MapIndex(indexes.RealTimeSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr="title")
    date = indexes.DateTimeField(model_attr="last_modified")
    iid = indexes.IntegerField(model_attr='id')
    type = indexes.CharField(faceted=True)
    json = indexes.CharField(indexed=False)

    def get_model(self):
        return Map

    def prepare_type(self, obj):
        return "map"

    def prepare_json(self, obj):
        data = {
            "_type": self.prepare_type(obj),			
            "id": obj.id,
            "last_modified": obj.last_modified.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "title": obj.title,
            "description": obj.abstract,
            "owner": obj.owner.username,
            "keywords": [keyword.name for keyword in obj.keywords.all()] if obj.keywords else [], 
            "thumb": Thumbnail.objects.get_thumbnail(obj),
            "detail_url": obj.get_absolute_url(),
        }

        if obj.owner:
            data.update({"owner_detail": Contact.objects.get(user=obj.owner).get_absolute_url()})

        return json.dumps(data)
