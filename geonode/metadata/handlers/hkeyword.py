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

from django.utils.translation import gettext as _

from geonode.metadata.handlers.abstract import MetadataHandler
from geonode.resource.utils import KeywordHandler

logger = logging.getLogger(__name__)


class HKeywordHandler(MetadataHandler):

    def update_schema(self, jsonschema, context, lang=None):
        hkeywords = {
            "type": "array",
            "title": _("Keywords"),
            "description": _("Hierarchical keywords"),
            "items": {
                "type": "string",
            },
            "ui:options": {
                "geonode-ui:autocomplete": {
                    "url": reverse("metadata_autocomplete_hkeywords"),
                    "creatable": True,
                },
            },
            "geonode:handler": "hkeyword",
        }

        self._add_subschema(jsonschema, "hkeywords", hkeywords, after_what="tkeywords")
        return jsonschema

    def get_jsonschema_instance(self, resource, field_name, context, errors, lang=None):
        return [keyword.name for keyword in resource.keywords.all()]

    def update_resource(self, resource, field_name, json_instance, context, errors, **kwargs):
        # TODO: see also resourcebase_form.disable_keywords_widget_for_non_superuser(request.user)
        hkeywords = json_instance["hkeywords"]
        cleaned = [k for k in hkeywords if k]
        logger.debug(f"hkeywords: {hkeywords} --> {cleaned}")
        KeywordHandler(resource, cleaned).set_keywords()
