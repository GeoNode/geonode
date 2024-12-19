import os
from geonode.settings import PROJECT_ROOT

MODEL_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "{GEONODE_SITE}/resource.json",
    "title": "GeoNode resource",
    "type": "object",
    "properties": {},
}

# The base schema is defined as a file in order to be customizable from other GeoNode instances
JSONSCHEMA_BASE = os.path.join(PROJECT_ROOT, "metadata/schemas/base.json")

METADATA_HANDLERS = {
    "base": "geonode.metadata.handlers.base.BaseHandler",
    "thesaurus": "geonode.metadata.handlers.thesaurus.TKeywordsHandler",
    "hkeyword": "geonode.metadata.handlers.hkeyword.HKeywordHandler",
    "region": "geonode.metadata.handlers.region.RegionHandler",
    "group": "geonode.metadata.handlers.group.GroupHandler",
    "doi": "geonode.metadata.handlers.doi.DOIHandler",
    "linkedresource": "geonode.metadata.handlers.linkedresource.LinkedResourceHandler",
    "contact": "geonode.metadata.handlers.contact.ContactHandler",
    "sparse": "geonode.metadata.handlers.sparse.SparseHandler",
}
