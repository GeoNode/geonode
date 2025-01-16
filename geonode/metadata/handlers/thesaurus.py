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

import logging

from rest_framework.reverse import reverse

from django.db.models import Q
from django.utils.translation import gettext as _

from geonode.base.models import Thesaurus, ThesaurusKeyword, ThesaurusKeywordLabel
from geonode.metadata.handlers.abstract import MetadataHandler


logger = logging.getLogger(__name__)


TKEYWORDS = "tkeywords"


class TKeywordsHandler(MetadataHandler):
    """
    Handles the keywords for all the Thesauri with max card > 0
    """

    @staticmethod
    def collect_thesauri(filter, lang=None):
        # this query return the list of thesaurus X the list of localized titles
        q = (
            Thesaurus.objects.filter(filter)
            .values(
                "id",
                "identifier",
                "title",
                "description",
                "order",
                "card_min",
                "card_max",
                "rel_thesaurus__label",
                "rel_thesaurus__lang",
            )
            .order_by("order")
        )

        # We don't know if we have the title for the requested lang: so let's loop on all retrieved translations
        collected_thesauri = {}
        for r in q.all():
            identifier = r["identifier"]
            thesaurus = collected_thesauri.get(identifier, {})
            if not thesaurus:
                # init
                logger.debug(f"Initializing Thesaurus {lang}/{identifier} JSON Schema")
                collected_thesauri[identifier] = thesaurus
                thesaurus["id"] = r["id"]
                thesaurus["card"] = {}
                thesaurus["card"]["minItems"] = r["card_min"]
                if r["card_max"] != -1:
                    thesaurus["card"]["maxItems"] = r["card_max"]
                thesaurus["title"] = r["title"]  # default title
                thesaurus["description"] = r["description"]  # not localized in db

            # check if this is the localized record we're looking for
            if r["rel_thesaurus__lang"] == lang:
                logger.debug(f"Localizing Thesaurus {identifier} JSON Schema for lang {lang}")
                thesaurus["title"] = r["rel_thesaurus__label"]

        return collected_thesauri

    def update_schema(self, jsonschema, context, lang=None):

        collected_thesauri = self.collect_thesauri(~Q(card_max=0), lang=lang)

        # copy info to json schema
        thesauri = {}
        for id, ct in collected_thesauri.items():
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
                        },
                    },
                },
                "ui:options": {
                    "geonode-ui:autocomplete": reverse(
                        "metadata_autocomplete_tkeywords", kwargs={"thesaurusid": ct["id"]}
                    )
                },
            }

            thesaurus.update(ct["card"])
            thesauri[id] = thesaurus

        tkeywords = {
            "type": "object",
            "title": _("Keywords from Thesaurus"),
            "description": _("List of keywords from Thesaurus"),
            "geonode:handler": "thesaurus",
            "properties": thesauri,
        }

        # We are going to hide the tkeywords property if there's no thesaurus configured
        # We can't remove the property altogether, since hkeywords relies on tkeywords for positioning
        if not thesauri:
            tkeywords["ui:widget"] = "hidden"

        # add thesauri after category
        self._add_subschema(jsonschema, TKEYWORDS, tkeywords, after_what="category")

        return jsonschema

    def get_jsonschema_instance(self, resource, field_name, context, errors, lang=None):
        tks = {}
        for tk in resource.tkeywords.all():
            tks[tk.id] = tk
        tkls = ThesaurusKeywordLabel.objects.filter(
            keyword__id__in=tks.keys(), lang=lang
        )  # read all entries in a single query

        ret = {}
        for tkl in tkls:
            keywords = ret.setdefault(tkl.keyword.thesaurus.identifier, [])
            keywords.append({"id": tkl.keyword.about, "label": tkl.label})
            del tks[tkl.keyword.id]

        if tks:
            logger.info(f"Returning untranslated '{lang}' keywords: {tks}")
            for tk in tks.values():
                keywords = ret.setdefault(tk.thesaurus.identifier, [])
                keywords.append({"id": tk.about, "label": tk.alt_label})

        return ret

    def update_resource(self, resource, field_name, json_instance, context, errors, **kwargs):
        kids = []
        for thes_id, keywords in json_instance.get(TKEYWORDS, {}).items():
            logger.info(f"Getting info for thesaurus {thes_id}")
            for keyword in keywords:
                kids.append(keyword["id"])

        kw_requested = ThesaurusKeyword.objects.filter(about__in=kids)
        resource.tkeywords.set(kw_requested)
