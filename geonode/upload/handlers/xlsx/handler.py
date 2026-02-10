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
import os
import shlex
from distutils.util import strtobool
from pathlib import Path
import csv
from datetime import datetime
import math
from celery import group
from python_calamine import CalamineWorkbook
from osgeo import ogr

from dynamic_models.models import ModelSchema

from geonode.upload.handlers.common.vector import BaseVectorFileHandler
from geonode.upload.handlers.csv.handler import CSVFileHandler
from geonode.upload.celery_tasks import create_dynamic_structure
from geonode.upload.handlers.utils import GEOM_TYPE_MAPPING
from geonode.upload.api.exceptions import InvalidInputFileException

logger = logging.getLogger("importer")


class XLSXFileHandler(CSVFileHandler):

    XLSX_UPLOAD_ENABLED = strtobool(os.getenv("XLSX_UPLOAD_ENABLED", "False"))

    lat_names = CSVFileHandler.possible_lat_column
    lon_names = CSVFileHandler.possible_long_column

    @classmethod
    def is_xlsx_enabled(cls):
        """
        Unified check for the feature toggle.
        Returns True if enabled, None if disabled.
        """
        if not cls.XLSX_UPLOAD_ENABLED:
            return None
        return True

    @property
    def supported_file_extension_config(self):

        # If disabled, return an empty list or None so the UI doesn't show XLSX options
        if not self.is_xlsx_enabled():
            return None

        return {
            "id": "excel",  # Use a generic ID that doesn't imply a specific extension
            "formats": [
                {
                    "label": "Excel (OpenXML)",
                    "required_ext": ["xlsx"],
                    "optional_ext": ["sld", "xml"],
                },
                {
                    "label": "Excel (Binary/Legacy)",
                    "required_ext": ["xls"],
                    "optional_ext": ["sld", "xml"],
                },
            ],
            "actions": list(self.TASKS.keys()),
            "type": "vector",
        }

    @staticmethod
    def can_handle(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        # Availability Check for the back-end
        if not XLSXFileHandler.is_xlsx_enabled():
            return False

        base = _data.get("base_file")
        if not base:
            return False

        # Support both XLSX and XLS
        valid_extensions = (".xlsx", ".xls")

        is_excel = (
            base.lower().endswith(valid_extensions)
            if isinstance(base, str)
            else base.name.lower().endswith(valid_extensions)
        )

        return is_excel and BaseVectorFileHandler.can_handle(_data)

    @staticmethod
    def is_valid(files, user, **kwargs):
        from geonode.upload.utils import UploadLimitValidator

        # Basic GeoNode validation
        BaseVectorFileHandler.is_valid(files, user)

        # Parallelism check (This is fast and doesn't need to open the file)
        upload_validator = UploadLimitValidator(user)
        upload_validator.validate_parallelism_limit_per_user()

        # We handle the deep inspection (lat/lon) later.
        return True

    @staticmethod
    def create_ogr2ogr_command(files, original_name, ovverwrite_layer, alternate, **kwargs):
        """
        Customized for XLSX: Only looks for X/Y (Point) data.
        Sanitized with shlex.quote to prevent Command Injection.
        """
        # Sanitize user-controlled strings immediately
        safe_original_name = shlex.quote(original_name)
        safe_alternate = shlex.quote(alternate)

        # Pass the safe versions to the base handler
        base_command = BaseVectorFileHandler.create_ogr2ogr_command(
            files, safe_original_name, ovverwrite_layer, safe_alternate
        )

        # Define mapping (these are safe as they are class-level constants)
        lat_mapping = ",".join(XLSXFileHandler.lat_names)
        lon_mapping = ",".join(XLSXFileHandler.lon_names)

        additional_option = f' -oo "X_POSSIBLE_NAMES={lon_mapping}" ' f'-oo "Y_POSSIBLE_NAMES={lat_mapping}"'

        # Return the combined, safe command string
        return (
            f"{base_command} -oo KEEP_GEOM_COLUMNS=NO "
            f"-lco GEOMETRY_NAME={BaseVectorFileHandler().default_geometry_column_name} "
            f"{additional_option}"
        )

    def create_dynamic_model_fields(
        self,
        layer: str,
        dynamic_model_schema: ModelSchema = None,
        overwrite: bool = None,
        execution_id: str = None,
        layer_name: str = None,
        return_celery_group: bool = True,
    ):
        # retrieving the field schema from ogr2ogr and converting the type to Django Types
        layer_schema = [{"name": x.name.lower(), "class_name": self._get_type(x), "null": True} for x in layer.schema]

        class_name = GEOM_TYPE_MAPPING.get(self.promote_to_multi("Point"))
        # Get the geometry type name from OGR (e.g., 'Point' or 'Point 25D')
        geom_type_name = ogr.GeometryTypeToName(layer.GetGeomType())

        layer_schema += [
            {
                "name": layer.GetGeometryColumn() or self.default_geometry_column_name,
                "class_name": class_name,
                "dim": (3 if geom_type_name.lower().startswith("3d") or "z" in geom_type_name.lower() else 2),
            }
        ]

        if not return_celery_group:
            return layer_schema

        list_chunked = [layer_schema[i : i + 30] for i in range(0, len(layer_schema), 30)]
        celery_group = group(
            create_dynamic_structure.s(execution_id, schema, dynamic_model_schema.id, overwrite, layer_name)
            for schema in list_chunked
        )

        return dynamic_model_schema, celery_group

    def pre_processing(self, files, execution_id, **kwargs):
        from geonode.upload.orchestrator import orchestrator

        # calling the super function (CSVFileHandler logic)
        _data, execution_id = super().pre_processing(files, execution_id, **kwargs)

        # convert the XLSX file into a CSV
        xlsx_file = _data.get("files", {}).get("base_file", "")
        if not xlsx_file:
            raise InvalidInputFileException(detail="The base file was not found in the upload payload.")

        output_file = str(Path(xlsx_file).with_suffix(".csv"))

        try:
            workbook = CalamineWorkbook.from_path(xlsx_file)

            # Sheet Validation (Uses the validated sheet name)
            sheet_name = self._validate_sheets(workbook)
            sheet = workbook.get_sheet_by_name(sheet_name)

            # We iterate until we find the first non-empty row
            rows_gen = iter(sheet.to_python())
            try:
                # We strictly take the first row. No skipping allowed.
                headers = next(rows_gen)
            except StopIteration:
                raise InvalidInputFileException(detail="The file is empty.")

            # Restrictive File Structure Validation
            self._validate_headers(headers)

            # Conversion with row cleanup
            # Note: rows_gen continues from the row after the headers
            self._convert_to_csv(headers, rows_gen, output_file)

        except Exception as e:
            logger.exception("XLSX Pre-processing failed")
            raise InvalidInputFileException(detail=f"Failed to securely parse Excel: {str(e)}")

        # update the file path in the payload
        _data["files"]["base_file"] = output_file

        if "temporary_files" not in _data or not isinstance(_data["temporary_files"], dict):
            _data["temporary_files"] = {}

        _data["temporary_files"]["base_file"] = output_file

        # updating the execution id params
        orchestrator.update_execution_request_obj(
            orchestrator.get_execution_object(execution_id), {"input_params": _data}
        )
        return _data, execution_id

    def _validate_sheets(self, workbook):
        """Returns the first sheet name and logs warnings if others exist."""
        sheets = workbook.sheet_names
        if not sheets:
            raise InvalidInputFileException(detail="No sheets found in workbook.")
        if len(sheets) > 1:
            logger.warning(f"Multiple sheets found. Ignoring: {sheets[1:]}")
        return sheets[0]

    def _validate_headers(self, headers):
        """
        Strictly validates Row 1 for headers:
        - Must not be empty.
        - Must contain geometry 'fingerprints' (Lat/Lon).
        - Must have unique and non-empty column names.
        """
        # Existence Check
        if not headers or self._detect_empty_rows(headers):
            raise InvalidInputFileException(detail="No data or headers found in the selected sheet.")

        # Normalization
        clean_headers = [str(h).strip().lower() if h is not None else "" for h in headers]

        # Geometry Fingerprint Check
        has_lat = any(h in self.lat_names for h in clean_headers)
        has_lon = any(h in self.lon_names for h in clean_headers)

        if not (has_lat and has_lon):
            raise InvalidInputFileException(
                detail="The headers do not contain valid geometry headers. "
                "GeoNode requires Latitude and Longitude labels in the first row."
            )

        # Integrity Check (No Empty Names)
        if any(h == "" for h in clean_headers):
            raise InvalidInputFileException(detail="One or more columns in the first row are missing a header name.")

        # Uniqueness Check
        if len(clean_headers) != len(set(clean_headers)):
            duplicates = set([h for h in clean_headers if clean_headers.count(h) > 1])
            raise InvalidInputFileException(detail=f"Duplicate headers found in Row 1: {', '.join(duplicates)}")

        return True

    def _data_sense_check(self, x, y):
        """
        High-speed coordinate validation for large datasets
        """
        try:
            # Catch Excel Date objects immediately (Calamine returns these as datetime)
            if isinstance(x, datetime) or isinstance(y, datetime):
                return False

            f_x = float(x)
            f_y = float(y)

            # Finiteness check (Catches NaN, Inf, and None)
            # This is extremely fast in Python
            if not (math.isfinite(f_x) and math.isfinite(f_y)):
                return False

            # Magnitude check
            # Limits to +/- 40 million (covers all CRS including Web Mercator)
            # but blocks 'serial date numbers' or corrupted scientific notation
            if not (-40000000 < f_x < 40000000 and -40000000 < f_y < 40000000):
                return False

            return True
        except (ValueError, TypeError):
            return False

    def _detect_empty_rows(self, row):
        return not row or all(cell is None or str(cell).strip() == "" for cell in row)

    def _convert_to_csv(self, headers, rows_gen, output_path):
        """Streams valid data to CSV, skipping empty rows."""

        # Define clean_headers once here to find the indices
        clean_headers = [str(h).strip().lower() for h in headers]

        # Get the indices for the Lat and Lon columns
        lat_idx = next(i for i, h in enumerate(clean_headers) if h in self.lat_names)
        lon_idx = next(i for i, h in enumerate(clean_headers) if h in self.lon_names)

        # Local binding of the check function for loop speed
        check_func = self._data_sense_check

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for row_num, row in enumerate(rows_gen, start=2):
                # Skip row if it contains no data
                if self._detect_empty_rows(row):
                    continue

                if not check_func(row[lon_idx], row[lat_idx]):
                    raise InvalidInputFileException(
                        detail=f"Coordinate error at row {row_num}. "
                        "Check for dates or non-numeric values in Lat/Lon."
                    )

                writer.writerow(row)
