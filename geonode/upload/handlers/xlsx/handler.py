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

from geonode.upload.handlers.common.vector import BaseVectorFileHandler
from geonode.upload.handlers.csv.handler import CSVFileHandler

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


    def pre_processing(self, files, execution_id, **kwargs):
        from geonode.upload.orchestrator import orchestrator
        import pandas as pd
        # calling the super function
        _data, execution_id = super().pre_processing(files, execution_id, **kwargs)
        # convert the XLSX file into a CSV
        xlsx_file = _data.get("files", {}).get("base_file", "")
        if not xlsx_file:
            raise Exception("File not found")
        output_file = str(Path(xlsx_file).with_suffix('.csv'))
        
        wb = pd.read_excel(xlsx_file, parse_dates=False, engine='calamine', dtype={
            "latitude": float,
            "longitude": float
        })
        wb.to_csv(output_file, index=False)
        
        # update the file path in the payload
        _data['files']['base_file'] = output_file
        _data['temporary_files']['base_file'] = output_file
        
        # updating the execution id params
        orchestrator.update_execution_request_obj(orchestrator.get_execution_object(execution_id), {"input_params": _data})
        return _data, execution_id
        