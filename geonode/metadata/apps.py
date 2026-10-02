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


def setup_metadata_handlers():
    from geonode.metadata import settings as metadata_settings
    from geonode.metadata.manager import (
        metadata_manager,
        HANDLER_ORDER_INITIAL,
        HANDLER_ORDER_DEFAULT,
        HANDLER_ORDER_FINAL,
    )

    # the module is read now, and not imported by name, so that an external module redefining
    # one of the groups is taken into account
    groups = (
        (metadata_settings.INITIAL_METADATA_HANDLERS, HANDLER_ORDER_INITIAL),
        (metadata_settings.METADATA_HANDLERS, HANDLER_ORDER_DEFAULT),
        (metadata_settings.FINAL_METADATA_HANDLERS, HANDLER_ORDER_FINAL),
    )

    registered = {}
    for handlers, order in groups:
        for handler_id, module_path in handlers.items():
            if (previous := registered.get(handler_id)) is not None:
                # the last one would win silently, dragging the handler out of its group
                logger.warning(
                    f"Metadata handler '{handler_id}' is declared in more than one group "
                    f"(order {previous} and {order}): the latter is being used"
                )
            registered[handler_id] = order
            metadata_manager.add_handler(handler_id, import_string(module_path), order=order)

    metadata_manager.post_init()

    logger.info(f"Metadata handlers from config: {', '.join(metadata_manager.handlers)}")
