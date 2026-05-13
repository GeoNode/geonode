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
from rest_framework import serializers
from dynamic_rest.serializers import DynamicModelSerializer
from geonode.base.api.serializers import BaseDynamicModelSerializer
from geonode.base.models import ResourceBase
from geonode.upload.models import UploadParallelismLimit, UploadSizeLimit
from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.upload.zip_validation import ZipValidationError, is_zip_extension, validate_safe_zip


logger = logging.getLogger(__name__)


class BaseImporterSerializer(DynamicModelSerializer):
    """
    Base for every serializer wired into the importer endpoint.

    Holds the zip-safety check that must run for any ``base_file`` capable of
    carrying a zip-based archive (.zip / .kmz / .xlsx). DRF only invokes
    ``validate_base_file`` when the subclass declares a ``base_file`` field,
    so subclasses without one (e.g. RemoteResourceSerializer,
    EmptyDatasetSerializer) inherit harmlessly.
    """

    def validate_base_file(self, f):
        """
        Inspect the central directory of zip-based uploads (.zip for 3D Tiles
        and zipped shapefiles, .kmz, .xlsx) to reject path-traversal entries,
        symlinks, oversized archives and zip-bomb compression ratios before
        any handler extracts the file.
        """
        if not is_zip_extension(getattr(f, "name", None)):
            return f
        source = f.temporary_file_path() if hasattr(f, "temporary_file_path") else f
        try:
            validate_safe_zip(source)
        except ZipValidationError:
            logger.warning("ZIP validation failed for uploaded file.", exc_info=True)
            raise serializers.ValidationError("Invalid or unsafe ZIP archive.")
        finally:
            # Rewind any in-memory file-like we read so downstream code sees
            # the full stream.
            if hasattr(f, "seek"):
                try:
                    f.seek(0)
                except (OSError, ValueError):
                    pass
        return f


class ImporterSerializer(BaseImporterSerializer):
    class Meta:
        ref_name = "ImporterSerializer"
        model = ResourceBase
        view_name = "importer_upload"
        fields = (
            "base_file",
            "xml_file",
            "sld_file",
            "store_spatial_files",
            "skip_existing_layers",
            "action",
        )

    base_file = serializers.FileField()
    xml_file = serializers.FileField(required=False)
    sld_file = serializers.FileField(required=False)
    store_spatial_files = serializers.BooleanField(required=False, default=True)
    skip_existing_layers = serializers.BooleanField(required=False, default=False)
    action = serializers.CharField(required=False, default=exa.UPLOAD.value)


class OverwriteImporterSerializer(ImporterSerializer):
    class Meta:
        ref_name = "OverwriteImporterSerializer"
        model = ResourceBase
        view_name = "importer_upload"
        fields = ImporterSerializer.Meta.fields + ("resource_pk",)

    resource_pk = serializers.IntegerField(required=True)


class UploadSizeLimitSerializer(BaseDynamicModelSerializer):
    class Meta:
        model = UploadSizeLimit
        name = "upload-size-limit"
        view_name = "upload-size-limits-list"
        fields = (
            "slug",
            "description",
            "max_size",
            "max_size_label",
        )


class UploadParallelismLimitSerializer(BaseDynamicModelSerializer):
    class Meta:
        model = UploadParallelismLimit
        name = "upload-parallelism-limit"
        view_name = "upload-parallelism-limits-list"
        fields = (
            "slug",
            "description",
            "max_number",
        )
        read_only_fields = ("slug",)


class UpsertImporterSerializer(ImporterSerializer):
    class Meta:
        ref_name = "UpsertImporterSerializer"
        model = ResourceBase
        view_name = "importer_upload"
        fields = ImporterSerializer.Meta.fields + (
            "upsert_key",
            "resource_pk",
        )

    upsert_key = serializers.CharField(required=False, default="fid")
    resource_pk = serializers.IntegerField(required=True)
