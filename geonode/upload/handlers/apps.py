import logging

from django.apps import AppConfig
from django.conf import settings
from django.utils.module_loading import import_string


logger = logging.getLogger(__name__)


class HandlersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "geonode.upload.handlers"

    def ready(self):
        """Finalize setup"""
        run_setup_hooks()
        super(HandlersConfig, self).ready()


def run_setup_hooks(*args, **kwargs):
    if getattr(settings, "IMPORTER_HANDLERS", []):
        _handlers = [import_string(module_path) for module_path in settings.IMPORTER_HANDLERS]
        for item in _handlers:
            item.register()
        logger.info(f"The following handlers have been registered: {', '.join(settings.IMPORTER_HANDLERS)}")

        _available_settings = [
            import_string(module_path)().supported_file_extension_config
            for module_path in settings.IMPORTER_HANDLERS
            if import_string(module_path)().supported_file_extension_config
        ]
        # injecting the new config required for FE
        supported_type = [
            {
                "id": "xml",
                "label": "XML Metadata File",
                "format": "metadata",
                "ext": ["xml"],
                "mimeType": ["application/json"],
                "needsFiles": [
                    "shp",
                    "prj",
                    "dbf",
                    "shx",
                    "csv",
                    "tiff",
                    "zip",
                    "sld",
                    "geojson",
                ],
            },
            {
                "id": "sld",
                "label": "Styled Layer Descriptor (SLD)",
                "format": "metadata",
                "ext": ["sld"],
                "mimeType": ["application/json"],
                "needsFiles": [
                    "shp",
                    "prj",
                    "dbf",
                    "shx",
                    "csv",
                    "tiff",
                    "zip",
                    "xml",
                    "geojson",
                ],
            },
        ]
        supported_type.extend(_available_settings)
        if not getattr(settings, "ADDITIONAL_DATASET_FILE_TYPES", None):
            setattr(settings, "ADDITIONAL_DATASET_FILE_TYPES", supported_type)
        elif "gpkg" not in [x.get("id") for x in settings.ADDITIONAL_DATASET_FILE_TYPES]:
            settings.ADDITIONAL_DATASET_FILE_TYPES.extend(supported_type)
            setattr(
                settings,
                "ADDITIONAL_DATASET_FILE_TYPES",
                settings.ADDITIONAL_DATASET_FILE_TYPES,
            )
