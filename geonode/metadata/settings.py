import os
from geonode.settings import PROJECT_ROOT

MODEL_SCHEMA = {
                 "$schema": "https://json-schema.org/draft/2020-12/schema",
                 "$id": "{GEONODE_SITE}/resource.json",
                 "title": "GeoNode resource",
                 "type": "object",
                 "properties": {
                }
            }

# The base schema is defined as a file in order to be customizable from other GeoNode instances
JSONSCHEMA_BASE = os.path.join(PROJECT_ROOT, "core_schema.json")

METADATA_HANDLERS = [
    'geonode.metadata.handlers.CoreHandler',
]