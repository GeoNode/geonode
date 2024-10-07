import logging

from django.conf import settings
from django.http import HttpResponse
from django.utils.module_loading import import_string

from geonode.assets.models import Asset

logger = logging.getLogger(__name__)


class AssetDownloadHandlerInterface:

    def create_response(self, asset: Asset, attachment: bool = False, basename=None, path=None) -> HttpResponse:
        raise NotImplementedError()


class AssetHandlerInterface:

    def handled_asset_class(self):
        raise NotImplementedError()

    def create(self, title, description, type, owner, *args, **kwargs):
        raise NotImplementedError()

    def remove_data(self, asset: Asset, **kwargs):
        raise NotImplementedError()

    def replace_data(self, asset: Asset, files: list):
        raise NotImplementedError()

    def clone(self, asset: Asset) -> Asset:
        """
        Creates a copy in the DB and copies the underlying data as well
        """
        raise NotImplementedError()

    def create_link_url(self, asset: Asset) -> str:
        raise NotImplementedError()

    def get_download_handler(self, asset: Asset = None) -> AssetDownloadHandlerInterface:
        raise NotImplementedError()

    def get_storage_manager(self, asset=None):
        raise NotImplementedError()


class AssetHandlerRegistry:
    _registry = {}
    _default_handler = None

    def init_registry(self):
        self.register_asset_handlers()
        self.set_default_handler()

    def register_asset_handlers(self):
        for module_path in settings.ASSET_HANDLERS:
            handler = import_string(module_path)
            self.register(handler)
        logger.info(f"Registered Asset handlers: {', '.join(settings.ASSET_HANDLERS)}")

    def set_default_handler(self):
        # check if declared class is registered
        for handler in self._registry.values():
            if ".".join([handler.__class__.__module__, handler.__class__.__name__]) == settings.DEFAULT_ASSET_HANDLER:
                self._default_handler = handler
                break

        if self._default_handler is None:
            logger.error(f"Could not set default asset handler class {settings.DEFAULT_ASSET_HANDLER}")
        else:
            logger.info(f"Default Asset handler {settings.DEFAULT_ASSET_HANDLER}")

    def register(self, asset_handler_class):
        self._registry[asset_handler_class.handled_asset_class()] = asset_handler_class()

    def get_default_handler(self) -> AssetHandlerInterface:
        return self._default_handler

    def get_handler(self, asset):
        asset = asset.get_real_instance() if isinstance(asset, Asset) else asset
        asset_cls = asset if isinstance(asset, type) else asset.__class__
        ret = self._registry.get(asset_cls, None)
        if not ret:
            logger.warning(f"Could not find asset handler for {asset_cls}::{asset.__class__}")
            logger.warning("Available asset types:")
            for k, v in self._registry.items():
                logger.warning(f"{k} --> {v.__class__.__name__}")
        return ret


asset_handler_registry = AssetHandlerRegistry()
