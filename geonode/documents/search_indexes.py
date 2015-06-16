from haystack import indexes
from geonode.documents.models import Document


class DocumentIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr="title", boost=2)
    # https://github.com/toastdriven/django-haystack/issues/569 - Necessary for sorting
    title_sortable = indexes.CharField(indexed=False)
    oid = indexes.IntegerField(model_attr='id')
    type = indexes.CharField(faceted=True)
    bbox_left = indexes.FloatField(model_attr="bbox_x0", null=True)
    bbox_right = indexes.FloatField(model_attr="bbox_x1", null=True)
    bbox_top = indexes.FloatField(model_attr="bbox_y0", null=True)
    bbox_bottom = indexes.FloatField(model_attr="bbox_y1", null=True)
    abstract = indexes.CharField(model_attr='abstract', boost=1.5)
    owner = indexes.CharField(model_attr="owner", faceted=True, null=True)
    modified = indexes.DateTimeField(model_attr="date")
    detail_url = indexes.CharField(model_attr="get_absolute_url")
    popular_count = indexes.IntegerField(model_attr="popular_count", default=0)
    keywords = indexes.MultiValueField(model_attr="keyword_list", indexed=False, null=True, faceted=True)
    thumbnail_url = indexes.CharField(model_attr="thumbnail_url", null=True)

    def get_model(self):
        return Document

    def prepare_type(self, obj):
        return "document"

    def prepare_title_sortable(self, obj):
        return obj.title.lower().lstrip()
