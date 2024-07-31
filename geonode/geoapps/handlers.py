from geonode.geoapps.models import GeoApp
from geonode.resource.handler import BaseResourceHandler
import logging

logger = logging.getLogger()


class GeoAppHandler(BaseResourceHandler):
    @staticmethod
    def can_handle(instance):
        return isinstance(instance, GeoApp)

    def download_urls(self, **kwargs):
        logger.debug("Download is not available for maps")
        return []
