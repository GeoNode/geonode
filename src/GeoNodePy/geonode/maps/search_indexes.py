import json

from django.core.urlresolvers import reverse

from haystack import indexes

from geonode.maps.models import Layer, Map, Thumbnail


class LayerIndex(indexes.RealTimeSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr="title")
    date = indexes.DateTimeField(model_attr="date")

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
            "name": obj.name,
            "storeType": obj.storeType,
            "download_links": obj.download_links(),
            "owner": obj.metadata_author.name,
            "metadata_links": obj.metadata_links,
            "keywords": obj.keywords.split() if obj.keywords else [],
            "thumb": Thumbnail.objects.get_thumbnail(obj),

            "detail": obj.get_absolute_url(),  # @@@ Use Sites Framework?
        }

        if obj.owner:
            data.update({"owner_detail": reverse("profiles.views.profile_detail", args=(obj.owner.username,))})

        return json.dumps(data)


class MapIndex(indexes.RealTimeSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr="title")
    date = indexes.DateTimeField(model_attr="last_modified")

    type = indexes.CharField(faceted=True)
    json = indexes.CharField(indexed=False)

    def get_model(self):
        return Map

    def prepare_type(self, obj):
        return "map"

    def prepare_json(self, obj):
        data = {
            "_type": self.prepare_type(obj),
            "_display_type": obj.display_type,

            "id": obj.id,
            "last_modified": obj.last_modified.strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "title": obj.title,
            "abstract": obj.abstract,
            "owner": obj.metadata_author.name,
            "keywords": obj.keywords.split() if obj.keywords else [],
            "thumb": Thumbnail.objects.get_thumbnail(obj),

            "detail": obj.get_absolute_url(),
        }

        if obj.owner:
            data.update({"owner_detail": reverse("profiles.views.profile_detail", args=(obj.owner.username,))})

        return data
