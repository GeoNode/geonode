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
from rest_framework import serializers

from geonode.base.models import ResourceBase
from geonode.upload.api.serializer import BaseImporterSerializer
from geonode.upload.utils import ImporterRequestAction as ira
from geonode.utils import is_safe_url


class DocumentImporterSerializer(BaseImporterSerializer):
    class Meta:
        ref_name = "DocumentImporterSerializer"
        model = ResourceBase
        view_name = "importer_upload"
        fields = ("base_file", "url", "title", "extension", "resource_pk", "action", "is_empty")

    base_file = serializers.FileField(required=False)
    url = serializers.URLField(required=False, help_text="URL of the remote document")
    title = serializers.CharField(required=False)
    extension = serializers.CharField(required=False)
    resource_pk = serializers.IntegerField(required=False)
    action = serializers.CharField(required=True)
    is_empty = serializers.SerializerMethodField()

    def get_is_empty(self, attrs):
        # a clone carries no file, the upload endpoint must skip the cloning of the files
        return attrs.get("action") == ira.DOCUMENT_CLONE.value

    def validate(self, attrs):
        """
        A document is a file or a remote url, as the document form requires.
        A clone has none of them: the document to clone and the title of the new one are the only input
        """
        if attrs.get("action") == ira.DOCUMENT_CLONE.value:
            if not attrs.get("title") or not attrs.get("resource_pk"):
                raise serializers.ValidationError("The title and the resource_pk are required to clone a document.")
            return attrs

        if not attrs.get("base_file") and not attrs.get("url"):
            raise serializers.ValidationError("Document must be a file or url.")

        if attrs.get("base_file") and attrs.get("url"):
            raise serializers.ValidationError("A document cannot have both a file and a url.")

        if attrs.get("action") == ira.DOCUMENT_REPLACE.value and not attrs.get("resource_pk"):
            raise serializers.ValidationError("The resource_pk is required to replace a document.")

        return attrs

    def validate_url(self, url):
        if not is_safe_url(url):
            raise serializers.ValidationError("URL is not allowed.")
        return url
