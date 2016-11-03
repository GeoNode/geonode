from haystack import indexes
from geonode.datarequests.models import DataRequestProfile


class DataRequestProfileIndex(indexes.SearchIndex, indexes.Indexable):
    oid = indexes.IntegerField(model_attr='id')
    first_name = indexes.CharField(model_attr='first_name', null=True)
    last_name = indexes.CharField(model_attr='last_name', null=True)
    middle_name = indexes.CharField(model_attr='midle_name', null=True)
    request_status = indexes.CharField(model_attr='request_status', faceted=True, null=True)
    requester_type = indexes.CharField(model_attr='requester_type', faceted=True, null=True)
    organization = indexes.CharField(model_attr='organization', null=True)
    organization_type = indexes.CharField(model_attr='organization_type', null=True)
    organization_other = indexes.CharField(model_attr='organization_other', null=True)
    type = indexes.CharField(faceted=True)

    def get_model(self):
        return DataRequestProfile

    def prepare_title(self, obj):
        return obj.first_name

    def prepare_title_sort(self, obj):
        return obj.first_name.lower().lstrip()

    def prepare_type(self, obj):
        return "datarequestprofile"
