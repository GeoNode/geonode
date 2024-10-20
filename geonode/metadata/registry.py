from django.utils.module_loading import import_string
from geonode.metadata.settings import METADATA_HANDLERS
import logging

logger = logging.getLogger(__name__)


class MetadataHandlersRegistry:

    handler_registry = {}

    def init_registry(self):
        self.register()
        logger.info(
            f"The following metadata handlers have been registered: {', '.join(METADATA_HANDLERS)}"
        )

    def register(self):
        for handler_id, module_path in METADATA_HANDLERS.items():
            self.handler_registry[handler_id] = import_string(module_path)

    @classmethod
    def get_registry(cls):
        return MetadataHandlersRegistry.handler_registry


metadata_registry = MetadataHandlersRegistry()