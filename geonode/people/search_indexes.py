import json

from django.conf import settings
from django.core.urlresolvers import reverse

from haystack import indexes

from geonode.people.models import Contact 

class ContactIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField()

    type = indexes.CharField(faceted=True)
    json = indexes.CharField(indexed=False)

    def get_model(self):
        return Contact

    def prepare_title(self, obj):
        return str(obj)

    def prepare_type(self, obj):
        return "contact"

    def prepare_json(self, obj):
        data = {
            "_type": self.prepare_type(obj),

            "username": obj.user.username if obj.user else None,

            "name": obj.name,
            "organization": obj.organization,
            "position": obj.position,
            "voice": obj.voice,
            "fax": obj.fax,
            "delivery": obj.delivery,
            "city": obj.city,
            "area": obj.area,
            "zipcode": obj.zipcode,
            "country": obj.country,
            "email": obj.email,

            "thumb": settings.STATIC_URL + "static/img/contact.png",
            "detail": None,
        }

        return json.dumps(data)
