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
from pathlib import Path
import csv
from python_calamine import CalamineWorkbook

from geonode.upload.handlers.common.vector import BaseVectorFileHandler
from geonode.upload.handlers.csv.handler import CSVFileHandler
from geonode.upload.utils import UploadLimitValidator
from geonode.upload.api.exceptions import (
            UploadParallelismLimitException, 
            InvalidInputFileException 
        )
from osgeo import ogr

logger = logging.getLogger("importer")


class XLSXFileHandler(CSVFileHandler):

    @property
    def supported_file_extension_config(self):
        return {
            "id": "xlsx",
            "formats": [
                {
                    "label": "XLSX",
                    "required_ext": ["xlsx"],
                    "optional_ext": ["sld", "xml"],
                }
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
        base = _data.get("base_file")
        if not base:
            return False
        return (
            base.lower().endswith(".xlsx") or base.lower().endswith(".xls")
            if isinstance(base, str)
            else base.name.lower().endswith(".xlsx") or base.name.lower().endswith(".xlsx")
        ) and BaseVectorFileHandler.can_handle(_data)

    
    @staticmethod
    def is_valid(files, user, **kwargs):
        BaseVectorFileHandler.is_valid(files, user)
        
        upload_validator = UploadLimitValidator(user)
        upload_validator.validate_parallelism_limit_per_user()
        actual_upload = upload_validator._get_parallel_uploads_count()
        max_upload = upload_validator._get_max_parallel_uploads()

        datasource = ogr.GetDriverByName("CSV").Open(files.get("base_file"))
        if not datasource:
            raise InvalidInputFileException("The converted XLSX data is invalid; no layers found.")

        layers = [datasource.GetLayer(i) for i in range(datasource.GetLayerCount())]
        layers_count = len(layers)

        if layers_count >= max_upload:
            raise UploadParallelismLimitException(
                detail=f"The number of layers ({layers_count}) exceeds the limit of {max_upload}."
            )

        schema_keys = [x.name.lower() for layer in layers for x in layer.schema]
        
        has_lat = any(x in CSVFileHandler.possible_lat_column for x in schema_keys)
        has_long = any(x in CSVFileHandler.possible_long_column for x in schema_keys)

        if has_lat and not has_long:
            raise InvalidInputFileException(
                f"Longitude is missing. Supported names: {', '.join(CSVFileHandler.possible_long_column)}"
            )

        if not has_lat and has_long:
            raise InvalidInputFileException(
                f"Latitude is missing. Supported names: {', '.join(CSVFileHandler.possible_lat_column)}"
            )

        if not (has_lat and has_long):
            raise InvalidInputFileException(
                "XLSX uploads require both a Latitude and a Longitude column. "
                f"Accepted Lat: {', '.join(CSVFileHandler.possible_lat_column)}. "
                f"Accepted Lon: {', '.join(CSVFileHandler.possible_long_column)}."
            )

        return True
    
    def pre_processing(self, files, execution_id, **kwargs):
        from geonode.upload.orchestrator import orchestrator
        
        # calling the super function (CSVFileHandler logic)
        _data, execution_id = super().pre_processing(files, execution_id, **kwargs)
        
        # convert the XLSX file into a CSV
        xlsx_file = _data.get("files", {}).get("base_file", "")
        if not xlsx_file:
            raise Exception("File not found")
            
        output_file = str(Path(xlsx_file).with_suffix('.csv'))
        
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
            raise InvalidInputFileException(detail=f"Failed to securely parse XLSX: {str(e)}")
        
        # update the file path in the payload
        _data['files']['base_file'] = output_file
        _data['temporary_files']['base_file'] = output_file
        
        # updating the execution id params
        orchestrator.update_execution_request_obj(
            orchestrator.get_execution_object(execution_id), 
            {"input_params": _data}
        )
        return _data, execution_id
        
    def _validate_sheets(self, workbook):
        """Returns the first sheet name and logs warnings if others exist."""
        sheets = workbook.sheet_names
        if not sheets:
            raise Exception("No sheets found in workbook.")
        if len(sheets) > 1:
            logger.warning(f"Multiple sheets found. Ignoring: {sheets[1:]}")
        return sheets[0]
    
    def _validate_headers(self, headers):
        """
        Ensures the candidate row is a valid header row:
        -- Not empty.
        -- All column names are unique (required for DB import).
        -- No empty column names (required for schema creation).
        """
        # Basic Content Check
        if self._detect_empty_rows(headers):
            raise Exception("The first row found is empty. Column headers are required.")

        # Normalization and Empty Name Check
        # We strip whitespace and convert to string to check for valid names
        clean_headers = [str(h).strip().lower() if h is not None else "" for h in headers]
        
        if any(h == "" for h in clean_headers):
            raise Exception(
                "One or more columns are missing a header name. Every column must have a title."
            )

        # Uniqueness Check
        if len(clean_headers) != len(set(clean_headers)):
            duplicates = set([h for h in clean_headers if clean_headers.count(h) > 1])
            raise Exception(f"Duplicate column headers found: {', '.join(duplicates)}")

        return True
        
    def _detect_empty_rows(self, row):
        return not row or all(cell is None or str(cell).strip() == "" for cell in row)
    
    def _convert_to_csv(self, headers, rows_gen, output_path):
        """Streams valid data to CSV, skipping empty rows."""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in rows_gen:
                # Skip row if it contains no data
                if self._detect_empty_rows(row):
                    continue
                
                # Cleanup: handle Excel's float-based integers (1.0 -> 1)
                cleaned_row = [
                    int(cell) if isinstance(cell, float) and cell.is_integer() else cell 
                    for cell in row
                ]
                writer.writerow(cleaned_row)