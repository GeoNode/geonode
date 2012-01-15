from haystack import indexes

from geonode.maps.models import Layer


class LayerIndex(indexes.RealTimeSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    
    name = indexes.CharField(model_attr="name")
    
    spatial_representation_type = indexes.CharField(model_attr="spatial_representation_type", null=True)
    
    temporal_extent_start = indexes.DateField(model_attr="temporal_extent_start", null=True)
    temporal_extent_end = indexes.DateField(model_attr="temporal_extent_end", null=True)

    def get_model(self):
        return Layer
