from geonode.maps.models import Map
from geonode.resource.handler import BaseResourceHandler
import logging

logger = logging.getLogger()


class MapHandler(BaseResourceHandler):
    @staticmethod
    def can_handle(instance):
        return isinstance(instance, Map)

    def download_urls(self, **kwargs):
        logger.debug("Download is not available for maps")
        return []
