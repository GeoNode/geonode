from django.apps import AppConfig


class MetadataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "geonode.metadata"

    def ready(self):
        """Finalize setup"""
        run_setup_hooks()
        super(MetadataConfig, self).ready()


def run_setup_hooks(*args, **kwargs):
    from geonode.metadata.registry import metadata_registry
    from geonode.metadata.manager import metadata_manager

    # registry initialization
    metadata_registry.init_registry()
    handlers = metadata_registry.handler_registry

    for handler_id, handler in handlers.items():
        metadata_manager.add_handler(handler_id, handler)
