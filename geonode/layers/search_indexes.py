from agon_ratings.models import OverallRating
from dialogos.models import Comment
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg
from haystack import indexes
from geonode.maps.models import Layer


class LayerIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    oid = indexes.CharField(model_attr='resourcebase_ptr_id')
    uuid = indexes.CharField(model_attr='uuid')
    type = indexes.CharField(faceted=True)
    subtype = indexes.CharField(faceted=True)
    name = indexes.CharField(model_attr="name")
    title = indexes.CharField(model_attr="title", boost=2)
    title_sortable = indexes.CharField(indexed=False)  # Necessary for sorting
    description = indexes.CharField(model_attr="abstract", boost=1.5)
    owner = indexes.CharField(model_attr="owner", faceted=True, null=True)
    modified = indexes.DateTimeField(model_attr="date")
    category = indexes.CharField(
        model_attr="category__identifier",
        faceted=True,
        null=True)
    detail_url = indexes.CharField(model_attr="get_absolute_url")
    bbox_left = indexes.FloatField(model_attr="bbox_x0", null=True)
    bbox_right = indexes.FloatField(model_attr="bbox_x1", null=True)
    bbox_bottom = indexes.FloatField(model_attr="bbox_y0", null=True)
    bbox_top = indexes.FloatField(model_attr="bbox_y1", null=True)
    temporal_extent_start = indexes.DateTimeField(
        model_attr="temporal_extent_start",
        null=True)
    temporal_extent_end = indexes.DateTimeField(
        model_attr="temporal_extent_end",
        null=True)
    keywords = indexes.MultiValueField(
        model_attr="keyword_slug_list",
        null=True,
        faceted=True)
    regions = indexes.MultiValueField(
        model_attr="region_slug_list",
        null=True,
        faceted=True)
    popular_count = indexes.IntegerField(
        model_attr="popular_count",
        default=0,
        boost=20)
    share_count = indexes.IntegerField(model_attr="share_count", default=0)
    rating = indexes.IntegerField(null=True)
    num_ratings = indexes.IntegerField()
    num_comments = indexes.IntegerField()
    thumbnail_url = indexes.CharField(model_attr="thumbnail_url", null=True)

    def get_model(self):
        return Layer

    def prepare_type(self, obj):
        return "layer"

    def prepare_subtype(self, obj):
        if obj.storeType == "dataStore":
            return "vector"
        elif obj.storeType == "coverageStore":
            return "raster"
        elif obj.storeType == "remoteStore":
            return "remote"

    def prepare_download_links(self, obj):
        try:
            links = obj.download_links()
            prepped = [(ext, name.encode(), extra)
                       for ext, name, extra in links]
            return prepped
        except:
            return None

    def prepare_metadata_links(self, obj):
        try:
            return obj.metadata_links
        except:
            return None

    def prepare_rating(self, obj):
        ct = ContentType.objects.get_for_model(obj)
        try:
            rating = OverallRating.objects.filter(
                object_id=obj.pk,
                content_type=ct
            ).aggregate(r=Avg("rating"))["r"]
            return float(str(rating or "0"))
        except OverallRating.DoesNotExist:
            return 0.0

    def prepare_num_ratings(self, obj):
        ct = ContentType.objects.get_for_model(obj)
        try:
            return OverallRating.objects.filter(
                object_id=obj.pk,
                content_type=ct
            ).all().count()
        except OverallRating.DoesNotExist:
            return 0

    def prepare_num_comments(self, obj):
        try:
            return Comment.objects.filter(
                object_id=obj.pk,
                content_type=ContentType.objects.get_for_model(obj)
            ).all().count()
        except:
            return 0

    def prepare_title_sortable(self, obj):
        return obj.title.lower()
