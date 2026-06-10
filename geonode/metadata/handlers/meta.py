#########################################################################
#
# Copyright (C) 2026 OSGeo
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
from html import unescape
import re

from bs4 import BeautifulSoup

from geonode.base.models import ResourceBase
from geonode.metadata.handlers.abstract import MetadataHandler

logger = logging.getLogger(__name__)


class CleanupHandler(MetadataHandler):
    _HTML_LIKE_PATTERN = re.compile(r"<\s*/?\s*[a-zA-Z][^>]*>")
    _DANGEROUS_TAGS = ("script", "style", "noscript", "iframe", "object", "embed")

    @staticmethod
    def _preview(value, max_len=120):
        text = repr(value)
        return text if len(text) <= max_len else f"{text[: max_len - 1]}…"

    @classmethod
    def _sanitize_string(cls, value: str):
        normalized = unescape(value)
        if not cls._HTML_LIKE_PATTERN.search(normalized):
            return value, False

        soup = BeautifulSoup(normalized, "html.parser")
        for tag in soup(cls._DANGEROUS_TAGS):
            tag.decompose()

        sanitized = soup.get_text()
        return sanitized, sanitized != value

    def _sanitize_instance(self, value, context, errors, path=None):
        path = path or []

        if isinstance(value, dict):
            for key, nested_value in list(value.items()):
                nested_path = path + [str(key)]
                value[key] = self._sanitize_instance(nested_value, context, errors, nested_path)
            return value

        if isinstance(value, list):
            for idx, nested_value in enumerate(list(value)):
                nested_path = path + [f"[{idx}]"]
                value[idx] = self._sanitize_instance(nested_value, context, errors, nested_path)
            return value

        if isinstance(value, str):
            sanitized, changed = self._sanitize_string(value)
            if changed:
                logger.warning(
                    "Sanitized potentially unsafe metadata field '%s': %s -> %s",
                    ".".join(path) if path else "ROOT",
                    self._preview(value),
                    self._preview(sanitized),
                )
                self._set_error(
                    errors,
                    path[0:1],  # set error on root field
                    self.localize_message(context, "metadata_error_sanitized", {}),
                )
            return sanitized

        return value

    def update_schema(self, jsonschema: dict, context: dict, lang=None):
        return jsonschema

    def get_jsonschema_instance(
        self, resource: ResourceBase, field_name: str, context: dict, errors: dict, lang: str = None
    ):
        pass

    def update_resource(
        self, resource: ResourceBase, field_name: str, json_instance: dict, context: dict, errors: dict, **kwargs
    ):
        pass

    def pre_deserialization(self, resource, jsonschema: dict, instance: dict, partial: set, context: dict):
        errors = context["errors"]
        self._sanitize_instance(instance, context, errors)
