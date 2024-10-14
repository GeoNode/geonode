from django.apps import AppConfig
from django.utils.module_loading import import_string
import logging

class MetadataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "geonode.metadata"

    def ready(self):
        """Finalize setup"""
        run_setup_hooks()
        super(MetadataConfig, self).ready()

def run_setup_hooks(*args, **kwargs):
    from geonode.metadata.settings import METADATA_HANDLERS
    from geonode.metadata.manager import metadata_manager

    logger = logging.getLogger(__name__)

    _handlers = [
        import_string(module_path) for module_path in METADATA_HANDLERS
    ]
    for _handler in _handlers:
        metadata_manager.add_handler(_handler)
    logger.info(
        f"The following metadata handlers have been registered: {', '.join(METADATA_HANDLERS)}"
    )