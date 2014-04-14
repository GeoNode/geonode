import json

from django.conf import settings
from django.core.urlresolvers import reverse

from haystack import indexes

from geonode.people.models import Profile

class ProfileIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='name', null=True)
    title_sort = indexes.CharField(null=True, indexed=False) #For sorting
    user = indexes.CharField(model_attr='user', null=True)
    profile = indexes.CharField(model_attr='profile', null=True)
    organization = indexes.CharField(model_attr='organization', null=True)
    position = indexes.CharField(model_attr='position', null=True)
    type = indexes.CharField(faceted=True)
    iid = indexes.IntegerField(model_attr='id')

    def get_model(self):
        return Profile

    def prepare_title(self, obj):
        return str(obj)

    def prepare_title_sort(self,obj):
        return str(obj).lower().lstrip()

    def prepare_type(self, obj):
        return "user"
