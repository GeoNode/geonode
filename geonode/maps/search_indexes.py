from haystack import indexes
from geonode.maps.models import Map


class MapIndex(indexes.SearchIndex, indexes.Indexable):
    id = indexes.IntegerField(model_attr='id')
    abstract = indexes.CharField(model_attr="abstract", boost=1.5)
    category__gn_description = indexes.CharField(model_attr="category__gn_description", null=True)
    csw_type = indexes.CharField(model_attr="csw_type")
    csw_wkt_geometry = indexes.CharField(model_attr="csw_wkt_geometry")
    detail_url = indexes.CharField(model_attr="get_absolute_url")
    distribution_description = indexes.CharField(model_attr="distribution_description", null=True)
    distribution_url = indexes.CharField(model_attr="distribution_url", null=True)
    owner_username = indexes.CharField(model_attr="owner", faceted=True, null=True)
    popular_count = indexes.IntegerField(
        model_attr="popular_count",
        default=0,
        boost=20)
    share_count = indexes.IntegerField(model_attr="share_count", default=0)
    rating = indexes.IntegerField(null=True)
    srid = indexes.CharField(model_attr="srid")
    supplemental_information = indexes.CharField(model_attr="supplemental_information", null=True)
    thumbnail_url = indexes.CharField(model_attr="thumbnail_url", null=True)
    uuid = indexes.CharField(model_attr="uuid")
    title = indexes.CharField(model_attr="title", boost=2)
    date = indexes.DateTimeField(model_attr="date")

    text = indexes.CharField(document=True, use_template=True, stored=False)
    # https://github.com/toastdriven/django-haystack/issues/569 - Necessary for sorting
    title_sortable = indexes.CharField(model_attr="title", indexed=False, stored=False)
    type = indexes.CharField(faceted=True)
    bbox_left = indexes.FloatField(model_attr="bbox_x0", null=True, stored=False)
    bbox_right = indexes.FloatField(model_attr="bbox_x1", null=True, stored=False)
    bbox_top = indexes.FloatField(model_attr="bbox_y0", null=True, stored=False)
    bbox_bottom = indexes.FloatField(model_attr="bbox_y1", null=True, stored=False)
    category = indexes.CharField(
        model_attr="category__identifier",
        faceted=True,
        null=True,
        stored=False)

    def get_model(self):
        return Map

    def prepare_type(self, obj):
        return "map"

    def prepare_title_sortable(self, obj):
        return obj.title.lower()
