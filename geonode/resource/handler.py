from abc import ABC
import logging

logger = logging.getLogger(__file__)


class BaseResourceHandler(ABC):
    """
    Base abstract resource handler object
    define the required method needed to define a resource handler
    As first implementation it will take care of the download url
    and the download response for a resource
    """

    REGISTRY = []

    def __init__(self, instance=None) -> None:
        self.instance = instance

    def __str__(self):
        return f"{self.__module__}.{self.__class__.__name__}"

    def __repr__(self):
        return self.__str__()

    @classmethod
    def register(cls):
        BaseResourceHandler.REGISTRY.append(cls)

    @classmethod
    def get_registry(cls):
        return BaseResourceHandler.REGISTRY

    def get_handler_by_instance(self, instance):
        """
        Given a resource, should return it's handler
        """
        for handler in self.get_registry():
            if handler.can_handle(instance):
                return handler(instance)
        logger.error("No handlers found for the given resource")
        return self

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


resource_hander = BaseResourceHandler()
