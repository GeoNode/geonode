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

        thesauri = {}
        for r in q.all():
            identifier = r["identifier"]
            logger.info(f"Adding Thesaurus {identifier} to JSON Schema lang {lang}")

            thesaurus = {}
            thesauri[identifier] = thesaurus

            thesaurus["type"] = "object"

            title = r["title"]  ## todo i18n
            thesaurus["title"] = title
            thesaurus["description"] = r["description"]  # not localized in db

            keywords = {
                "type": "array",
                "minItems": r["card_min"]
            }

            if r["card_max"] != -1:
                keywords["maxItems"] =  r["card_max"]

            keywords.update({
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
                        kwargs={"thesaurusid": r["id"]})
                }
            })

            thesaurus["properties"] = {"keywords": keywords}

        tkeywords = {
            "type": "object",
            "title": _("Thesaurus keywords"),
            "description": _("Keywords from controlled vocabularies"),
            "geonode:handler": "thesaurus",
            "properties": thesauri,
        }

        jsonschema["properties"]["tkeywords"] = tkeywords

        return jsonschema

    def get_jsonschema_instance(self, resource: ResourceBase, field_name: str):

        return None

    def update_resource(self, resource: ResourceBase, field_name: str, content: dict, json_instance: dict):

        pass

    def load_context(self, resource: ResourceBase, context: dict):

        pass
