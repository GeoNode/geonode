from geonode.assets.utils import get_default_asset
from geonode.base.models import ResourceBase
from geonode.layers.models import Dataset
from geonode.resource.handler import BaseResourceHandler
import logging
from geonode.assets.handlers import asset_handler_registry
from geonode.layers.utils import get_download_handlers, get_default_dataset_download_handler

logger = logging.getLogger()


class Tiles3DHandler(BaseResourceHandler):
    @staticmethod
    def can_handle(instance):
        return isinstance(instance, ResourceBase) and instance.subtype == "3dtiles"

    def download_urls(self, **kwargs):
        """
        Specific method that return the download URL of the document
        """
        super().download_urls()
        asset = get_default_asset(self.instance)
        if asset is not None:
            asset_url = asset_handler_registry.get_handler(asset).create_download_url(asset)
            return [{"url": asset_url, "ajax_safe": True, "default": True}]


class DatasetHandler(BaseResourceHandler):
    @staticmethod
    def can_handle(instance):
        return isinstance(instance, Dataset)

    def download_urls(self, **kwargs):
        super().download_urls()
        """
        Specific method that return the download URL of the document
        """
        download_urls = []
        # lets get only the default one first to set it
        default_handler = get_default_dataset_download_handler()
        obj = default_handler(kwargs.get("request"), self.instance.alternate)
        if obj.download_url:
            download_urls.append({"url": obj.download_url, "ajax_safe": obj.is_ajax_safe, "default": True})
        # then let's prepare the payload with everything
        for handler in get_download_handlers():
            obj = handler(kwargs.get("request"), self.instance.alternate)
            if obj.download_url:
                download_urls.append({"url": obj.download_url, "ajax_safe": obj.is_ajax_safe, "default": False})
        return download_urls
