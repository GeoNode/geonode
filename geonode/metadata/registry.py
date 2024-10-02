from django.conf import settings
from django.utils.module_loading import import_string


class MetadataHandlersRegistry:

    REGISTRY = []

    def init_registry(self):
        self.register()

    def register(self):
        for module_path in settings.METADATA_HANDLERS:
            self.REGISTRY.append(import_string(module_path))

    def register_new_app(self, module_path):
        self.REGISTRY.append(import_string(module_path))
    
    @classmethod
    def get_registry(cls):
        return MetadataHandlersRegistry.REGISTRY


metadata_registry = MetadataHandlersRegistry()