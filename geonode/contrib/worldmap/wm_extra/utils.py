from geonode.geoserver.helpers import create_gs_thumbnail_geonode
from geonode.layers.models import Layer

def create_wm_thumbnail(instance, overwrite=False):
    """
    WorldMap doesn't use thumbnails from GeoServer, but just the ones from html.
    """
    # we use the standard way just for layers, not for maps
    if isinstance(instance, Layer):
        create_gs_thumbnail_geonode(instance)
    else:
        return None
