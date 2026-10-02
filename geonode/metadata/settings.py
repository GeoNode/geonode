import os
from geonode.settings import PROJECT_ROOT, SITEURL

MODEL_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": f"{SITEURL}/resource.json",
    "title": "GeoNode resource",
    "type": "object",
    "properties": {},
}

# The base schema is defined as a file in order to be customizable from other GeoNode instances
JSONSCHEMA_BASE = os.path.join(PROJECT_ROOT, "metadata/schemas/base.json")

# Handlers that shall run before any other one, whatever gets registered later
INITIAL_METADATA_HANDLERS = {
    "metadata_cleaner": "geonode.metadata.handlers.meta.CleanupHandler",
}

# The handlers an external module is expected to add to: they run in between the other two groups
METADATA_HANDLERS = {
    "base": "geonode.metadata.handlers.base.BaseHandler",
    "thesaurus": "geonode.metadata.handlers.thesaurus.TKeywordsHandler",
    "hkeyword": "geonode.metadata.handlers.hkeyword.HKeywordHandler",
    "region": "geonode.metadata.handlers.region.RegionHandler",
    "doi": "geonode.metadata.handlers.doi.DOIHandler",
    "linkedresource": "geonode.metadata.handlers.linkedresource.LinkedResourceHandler",
    "contact": "geonode.metadata.handlers.contact.ContactHandler",
    "sparse": "geonode.metadata.handlers.sparse.SparseHandler",
}

# Handlers that shall run after any other one, whatever gets registered later.
# multilang is here since it localizes the fields added by the handlers before it, its own included
FINAL_METADATA_HANDLERS = {
    "multilang": "geonode.metadata.handlers.multilang.MultiLangHandler",
}
