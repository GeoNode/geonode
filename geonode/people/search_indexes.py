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
    # Adding these attributes so that the search page functions with elastic search
    city = indexes.CharField(model_attr='city', null=True)
    country = indexes.CharField(model_attr='country', null=True)
    profile_detail_url = indexes.CharField(model_attr='get_absolute_url', null=True)
    avatar_100 = indexes.CharField(null=True)
    text = indexes.CharField(document=True, use_template=True)
    type = indexes.CharField(faceted=True)

    def prepare_avatar_100(self, obj):
        avatar = obj.avatar_set.first()
        if avatar:
            return avatar.avatar_url(100)
        return ''

    def get_model(self):
        return Profile

    def prepare_title(self, obj):
        return str(obj)

    def prepare_title_sort(self, obj):
        return str(obj).lower().lstrip()

    def prepare_type(self, obj):
        return "user"
