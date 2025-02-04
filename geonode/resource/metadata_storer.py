import logging
from geonode.resource.manager import update_resource

logger = logging.getLogger(__name__)


def store_metadata(instance, custom=None):
    if not custom:
        return instance
    try:
        return update_resource(instance, vals=custom)
    except Exception as e:
        logger.exception(e)
        logger.error(f"Failed to update instance with custom payload: {custom}")
    return instance
