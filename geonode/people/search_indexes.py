from haystack import indexes
from geonode.people.models import Profile


class ProfileIndex(indexes.SearchIndex, indexes.Indexable):
    id = indexes.IntegerField(model_attr='id')
    username = indexes.CharField(model_attr='username', null=True)
    first_name = indexes.CharField(model_attr='first_name', null=True)
    last_name = indexes.CharField(model_attr='last_name', null=True)
    profile = indexes.CharField(model_attr='profile', null=True)
    organization = indexes.CharField(model_attr='organization', null=True)
    position = indexes.CharField(model_attr='position', null=True)
    text = indexes.CharField(document=True, use_template=True)
    type = indexes.CharField(faceted=True)

    def get_model(self):
        return Profile

    def prepare_title(self, obj):
        return str(obj)

    def prepare_title_sort(self, obj):
        return str(obj).lower().lstrip()

    def prepare_type(self, obj):
        return "user"
