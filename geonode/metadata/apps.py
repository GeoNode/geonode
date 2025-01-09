import logging

from django.apps import AppConfig
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


class MetadataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "geonode.metadata"

    def ready(self):
        """Finalize setup"""
        run_setup_hooks()
        super(MetadataConfig, self).ready()


def run_setup_hooks(*args, **kwargs):
    setup_metadata_handlers()

    from geonode.metadata.signals import connect_signals

    connect_signals()


def setup_metadata_handlers():
    from geonode.metadata.manager import metadata_manager
    from geonode.metadata.settings import METADATA_HANDLERS

    ids = []
    for handler_id, module_path in METADATA_HANDLERS.items():
        handler = import_string(module_path)
        metadata_manager.add_handler(handler_id, handler)
        ids.append(handler_id)

    logger.info(f"Metadata handlers from config: {', '.join(METADATA_HANDLERS)}")
