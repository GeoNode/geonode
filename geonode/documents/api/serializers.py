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
        # name and extension determine where the document file lives on disk
        # and how it is served. POST/PUT are blocked at the http_method_names
        # layer; making them read-only locks them down on PATCH too.
        read_only_fields = ("name", "extension")
