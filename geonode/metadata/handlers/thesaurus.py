#########################################################################
#
# Copyright (C) 2024 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import json
import logging

from rest_framework.reverse import reverse

from django.db.models import Q
from django.utils.translation import gettext as _

from geonode.base.models import ResourceBase
from geonode.metadata.handlers.abstract import MetadataHandler
from geonode.metadata.settings import JSONSCHEMA_BASE
from geonode.base.enumerations import ALL_LANGUAGES


logger = logging.getLogger(__name__)


class TKeywordsHandler(MetadataHandler):
    """
    The base handler builds a valid empty schema with the simple
    fields of the ResourceBase model
    """

    def __init__(self):
        self.json_base_schema = JSONSCHEMA_BASE
        self.base_schema = None

    def update_schema(self, jsonschema, lang=None):

        from geonode.base.models import Thesaurus

        # this query return the list of thesaurus X the list of localized titles
        q = (
            Thesaurus.objects.filter(~Q(card_max=0))
            .values("id", "identifier", "title", "description", "order", "card_min", "card_max",
                    "rel_thesaurus__label", "rel_thesaurus__lang")
            .order_by("order")
        )

        # We don't know if we have the title for the requested lang: so let's loop on all retrieved translations
        collected_thesauri = {}
        for r in q.all():
            identifier = r["identifier"]
            thesaurus = collected_thesauri.get(identifier, {})
            if not thesaurus:
                # init
                logger.debug(f"Initializing Thesaurus {identifier} JSON Schema")
                collected_thesauri[identifier] = thesaurus
                thesaurus["id"] = r["id"]
                thesaurus["card"] = {}
                thesaurus["card"]["minItems"] = r["card_min"]
                if r["card_max"] != -1:
                    thesaurus["card"]["maxItems"] =  r["card_max"]
                thesaurus["title"] = r["title"]  # default title
                thesaurus["description"] = r["description"]  # not localized in db

            # check if this is the localized record we're looking for
            if r["rel_thesaurus__lang"] == lang:
                logger.debug(f"Localizing Thesaurus {identifier} JSON Schema for lang {lang}")
                thesaurus["title"] = r["rel_thesaurus__label"]

        # copy info to json schema
        thesauri = {}
        for id,ct in collected_thesauri.items():
            thesaurus = {
                "type": "array",
                "title": ct["title"],
                "description": ct["description"],
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "title": "keyword id",
                            "description": "The id of the keyword (usually a URI)",
                        },
                        "label": {
                            "type": "string",
                            "title": "Label",
                            "description": "localized label for the keyword",
                        }
                    }
                },
                 "ui:options": {
                     'geonode-ui:autocomplete': reverse(
                         "thesaurus-keywords_autocomplete",
                         kwargs={"thesaurusid": ct["id"]})
                 }
            }

            thesaurus.update(ct["card"])
            thesauri[id] = thesaurus

        tkeywords = {
            "type": "object",
            "title": _("Thesaurus keywords"),
            "description": _("Keywords from controlled vocabularies"),
            "geonode:handler": "thesaurus",
            "properties": thesauri,
            # "ui:options": {
            #     'geonode-ui:group': 'Thesauri grop'
            # }
        }

        # add thesauri after category
        self._add_after(jsonschema, "category", "tkeywords", tkeywords)

        return jsonschema

    def get_jsonschema_instance(self, resource: ResourceBase, field_name: str):

        return {}

    def update_resource(self, resource: ResourceBase, field_name: str, json_instance: dict):
        pass


    def load_context(self, resource: ResourceBase, context: dict):

        pass
