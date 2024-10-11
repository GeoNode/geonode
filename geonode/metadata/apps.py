from django.apps import AppConfig

class MetadataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "geonode.metadata"

    def ready(self):
        """Finalize setup"""
        run_setup_hooks()
        super(MetadataConfig, self).ready()

def run_setup_hooks(*args, **kwargs):
    from django.utils.module_loading import import_string
    from geonode.metadata.settings import METADATA_HANDLERS
    from geonode.metadata.manager import metadata_manager
    import logging

    logger = logging.getLogger(__name__)

    _handlers = [
        import_string(module_path) for module_path in METADATA_HANDLERS
    ]
    for _handler in _handlers:
        metadata_manager.add_handler(_handler)
    #logger.info(
    #    f"The following handlers have been registered: {', '.join(_handlers)}"
    #)