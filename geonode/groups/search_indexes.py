import json

from django.conf import settings

from haystack import indexes

from geonode.groups.models import GroupProfile


class GroupIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(boost=2)
    # https://github.com/toastdriven/django-haystack/issues/569 - Necessary for sorting
    title_sortable = indexes.CharField(indexed=False)
    description = indexes.CharField(model_attr='description', boost=1.5)
    id = indexes.IntegerField(model_attr='id')
    type = indexes.CharField(faceted=True)
    json = indexes.CharField(indexed=False)

    def get_model(self):
        return GroupProfile

    def prepare_title(self, obj):
        return str(obj)

    def prepare_title_sortable(self, obj):
        return str(obj).lower()

    def prepare_type(self, obj):
        return "group"

    def prepare_json(self, obj):
        data = {
            "_type": self.prepare_type(obj),

            "title": obj.title,
            "description": obj.description,
            "keywords": [keyword.name for keyword in obj.keywords.all()] if obj.keywords else [],
            "thumb": settings.STATIC_URL + "static/img/contact.png",
            "detail": None,
        }

        return json.dumps(data)
