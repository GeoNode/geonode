import json

from django.conf import settings
from django.core.urlresolvers import reverse

from haystack import indexes

from geonode.maps.models import Map
from geonode.people.models import Contact


class MapIndex(indexes.RealTimeSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr="title")
    date = indexes.DateTimeField(model_attr="last_modified")
    iid = indexes.IntegerField(model_attr='id')
    type = indexes.CharField(faceted=True)
    bbox_left = indexes.FloatField(model_attr='bbox_left')
    bbox_right = indexes.FloatField(model_attr='bbox_right')
    bbox_top = indexes.FloatField(model_attr='bbox_top')
    bbox_bottom = indexes.FloatField(model_attr='bbox_bottom')
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
            #"thumb": Thumbnail.objects.get_thumbnail(obj),
            "detail_url": obj.get_absolute_url(),
        }

        if obj.owner:
            data.update({"owner_detail": Contact.objects.get(user=obj.owner).get_absolute_url()})

        return json.dumps(data)
