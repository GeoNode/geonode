import os

from django.apps import apps

from geonode.base.management.command_utils import setup_logger
from geonode.base.management.commands.thesaurus_subcommands.load import load_thesaurus, ACTION_UPDATE

logger = setup_logger()


def autoload_thesauri():
    """
    Discover and load all thesauri (.rdf files) found in a `thesauri/` directory
    within each installed Django app. Uses the `update` action so existing entries
    are updated and new ones are created without duplicates.
    """
    loaded = 0
    for app_config in apps.get_app_configs():
        thesauri_dir = os.path.join(app_config.path, "thesauri")
        logger.debug(f"Looking for auto thesaurus in app '{app_config.name}' path: {thesauri_dir}")
        if not os.path.isdir(thesauri_dir):
            continue
        rdf_files = [f for f in os.listdir(thesauri_dir) if f.lower().endswith(".rdf")]
        for rdf_file in sorted(rdf_files):
            rdf_path = os.path.join(thesauri_dir, rdf_file)
            logger.info(f"Autoloading thesaurus from app '{app_config.name}': {rdf_path}")
            try:
                load_thesaurus(rdf_path, identifier=None, action=ACTION_UPDATE, log_details=False)
                loaded += 1
            except Exception as e:
                logger.error(f"Failed to load thesaurus '{rdf_path}': {e}", exc_info=True)
    logger.info(f"Autoload complete: {loaded} thesaurus file(s) loaded.")
