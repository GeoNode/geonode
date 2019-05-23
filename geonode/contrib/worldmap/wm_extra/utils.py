from geonode.layers.utils import create_gs_thumbnail_geonode
from geonode.layers.models import Layer
from geonode.geoserver.createlayer.utils import DATA_QUALITY_MESSAGE


def create_wm_thumbnail(instance, overwrite=False):
    """
    WorldMap doesn't use thumbnails from GeoServer, but just the ones from html.
    """
    # we use the standard way just for layers, not for maps
    if isinstance(instance, Layer):
        # layer created by createlayer application don't need a thumbnail
        if not instance.data_quality_statement == DATA_QUALITY_MESSAGE:
            create_gs_thumbnail_geonode(instance)
    else:
        return None
