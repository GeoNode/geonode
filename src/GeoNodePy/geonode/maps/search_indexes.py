import json

from django.conf import settings
from django.core.urlresolvers import reverse

from haystack import indexes

from geonode.maps.models import Layer, Map, Thumbnail, Contact


class LayerIndex(indexes.RealTimeSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr="title")
    date = indexes.DateTimeField(model_attr="date")
    #id = indexes.IntegerField()
    type = indexes.CharField(faceted=True)
    subtype = indexes.CharField(faceted=True)
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
            
    def prepare_metadata_links(self,obj):
        prepped = [(ext,name.encode(),extra) for ext,name,extra in obj]
        return prepped
      
    def prepare_json(self, obj):
        # Still need to figure out how to get the follow data:
        """
        {
            attribution: {
                href: "",
                title: ""
            },
            bbox: {
                minx: "-82.744",
                miny: "10.706",
                maxx: "-87.691",
                maxy: "15.031"
            },
        }
        """

        data = {
            "_type": self.prepare_type(obj),
            "_display_type": obj.display_type,

            "id": obj.id,
            "uuid": obj.uuid,
            "last_modified": obj.date.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "title": obj.title,
            "abstract": obj.abstract,
            #"name": obj.name,
            #"storeType": obj.storeType,
            #"download_links": obj.download_links(),
            #"owner": obj.metadata_author.name,
            #"metadata_links": obj.metadata_links,
            #"keywords": [keyword.name for keyword in obj.keywords.all()] if obj.keywords else [],
            #"thumb": Thumbnail.objects.get_thumbnail(obj),
            #"detail": obj.get_absolute_url(),  # @@@ Use Sites Framework?
            "subtype": self.prepare_subtype(obj),
            "name": obj.title,
            "description": obj.abstract,
            "owner": obj.metadata_author.name,
            #"owner_detail": obj.owner.get_absolute_url(),
            "organization": "",
            "created": "",
            "last_modified": obj.date.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "start": "",
            "end": "",
            "category": "",
            "keywords": [keyword.name for keyword in obj.keywords.all()] if obj.keywords else [],
            "language": "",
            "edition": "",
            "purpose": "",
            "constraints": "",
            "license": "",
            "supplemental": "",
            "distribution": "",
            "dqs": "",
            "rating": "",
            "comments": "",
            "views": "",
            "thumb": Thumbnail.objects.get_thumbnail(obj),
            "detail_url": obj.get_absolute_url(),  # @@@ Use Sites Framework?
            "download_links": self.prepare_metadata_links(obj.download_links()),
            "metadata_links": obj.metadata_links,
            #"bbox": {
            #    "minx": bbox[0],
            #    "miny": bbox[2],
            #    "maxx": bbox[1],
            #    "maxy": bbox[3],
            #},
            #"attribution": {
            #    "title": poc_profile.name,
            #    "href": poc_profile.get_absolute_url(),
            #},
        }

        if obj.owner:
            data.update({"owner_detail": obj.owner.get_absolute_url()})

        return json.dumps(data)


class MapIndex(indexes.RealTimeSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr="title")
    date = indexes.DateTimeField(model_attr="last_modified")
    #id = indexes.IntegerField()
    type = indexes.CharField(faceted=True)
    json = indexes.CharField(indexed=False)

    def get_model(self):
        return Map

    def prepare_type(self, obj):
        return "map"

    def prepare_json(self, obj):
        data = {
            "_type": self.prepare_type(obj),
            #"_display_type": obj.display_type,

            "id": obj.id,
            "last_modified": obj.last_modified.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "title": obj.title,
            "abstract": obj.abstract,
            "owner": obj.owner.username,
            "keywords": [keyword.name for keyword in obj.keywords.all()] if obj.keywords else [], 
            "thumb": Thumbnail.objects.get_thumbnail(obj),
            "detail_url": obj.get_absolute_url(),
        }

        if obj.owner:
            data.update({"owner_detail": Contact.objects.get(user=obj.owner).get_absolute_url()})

        return json.dumps(data)
