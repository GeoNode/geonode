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

from dynamic_rest.fields.fields import DynamicComputedField
from rest_framework import serializers
from geonode.base.api.serializers import ResourceBaseSerializer
from geonode.documents.models import Document

logger = logging.getLogger(__name__)


class GeonodeFilePathField(DynamicComputedField):
    def get_attribute(self, instance):
        return instance.files


class DocumentFieldField(DynamicComputedField):
    def get_attribute(self, instance):
        return instance.files


class DocumentSerializer(ResourceBaseSerializer):
    title = serializers.CharField(required=False)
    file_path = GeonodeFilePathField(required=False, write_only=True)
    doc_file = DocumentFieldField(required=False, write_only=True)

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
                    "file_path",
                    "doc_file",
                    "doc_url",
                )
            )
        )
