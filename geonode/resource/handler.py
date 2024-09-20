from abc import ABC
import logging

from django.conf import settings
from django.utils.module_loading import import_string

logger = logging.getLogger(__file__)


class ResourceHandlerRegistry:

    REGISTRY = []

    def init_registry(self):
        self.register()

    def register(self):
        for module_path in settings.RESOURCE_HANDLERS:
            self.REGISTRY.append(import_string(module_path))

    @classmethod
    def get_registry(cls):
        return ResourceHandlerRegistry.REGISTRY

    def get_handler(self, instance):
        """
        Given a resource, should return it's handler
        """
        for handler in self.get_registry():
            if handler.can_handle(instance):
                return handler(instance)
        logger.error("No handlers found for the given resource")
        return BaseResourceHandler()


class BaseResourceHandler(ABC):
    """
    Base abstract resource handler object
    define the required method needed to define a resource handler
    As first implementation it will take care of the download url
    and the download response for a resource
    """

    def __init__(self, instance=None) -> None:
        self.instance = instance

    def __str__(self):
        return f"{self.__module__}.{self.__class__.__name__}"

    def __repr__(self):
        return self.__str__()

    def download_urls(self, **kwargs):
        """
        return the download url for each resource
        """
        if not self.instance:
            logger.warning("No instance declared, so is not possible to return the download url")
            return None
        return []

    def download_response(self, **kwargs):
        """
        Return the download response for the resource
        """
        raise NotImplementedError()


resource_registry = ResourceHandlerRegistry()
