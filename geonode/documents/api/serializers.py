#########################################################################
#
# Copyright (C) 2020 OSGeo
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

from rest_framework import serializers
from geonode.base.api.serializers import ResourceBaseSerializer
from geonode.documents.models import Document

logger = logging.getLogger(__name__)


# Fields that must never be mutable via the document API (they can point a
# Document at an arbitrary server filesystem path or rename the stored file).
# POST/PUT are disabled entirely; PATCH-time enforcement lives in
# DocumentSerializer.update().
IMMUTABLE_DOCUMENT_FIELDS = frozenset({"name", "extension", "files"})


class DocumentSerializer(ResourceBaseSerializer):
    title = serializers.CharField(required=False)

    class Meta:
        model = Document
        name = "document"
        view_name = "documents-list"
        fields = list(
            set(
                ResourceBaseSerializer.Meta.fields
                + (
                    "uuid",
                    "name",
                    "href",
                    "subtype",
                    "extension",
                    "mime_type",
                    "doc_url",
                )
            )
        )

    def update(self, instance, validated_data):
        # Defense in depth: make sure PATCH payloads can never rewrite the
        # fields that determine where the document file lives on disk. Field
        # definitions that carried a file have already been dropped
        # (file_path, doc_file) -- this guards against anything that sneaks
        # through dynamic_rest / nested serializer magic.
        for field_name in IMMUTABLE_DOCUMENT_FIELDS:
            validated_data.pop(field_name, None)
        return super().update(instance, validated_data)
