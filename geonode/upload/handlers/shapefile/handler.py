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
import ast
import json
import logging
import codecs
from geonode.utils import get_supported_datasets_file_types
from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.upload.utils import UploadLimitValidator
from geonode.upload.handlers.common.vector import BaseVectorFileHandler
from osgeo import ogr
from pathlib import Path

from geonode.upload.handlers.shapefile.exceptions import InvalidShapeFileException
from geonode.upload.handlers.shapefile.serializer import OverwriteShapeFileSerializer, ShapeFileSerializer
from geonode.upload.utils import ImporterRequestAction as ira

logger = logging.getLogger("importer")


class ShapeFileHandler(BaseVectorFileHandler):
    """
    Handler to import Shapefile files into GeoNode data db
    It must provide the task_lists required to comple the upload
    """

    @property
    def supported_file_extension_config(self):
        return {
            "id": "shp",
            "formats": [
                {
                    "label": "ESRI Shapefile",
                    "required_ext": ["shp", "prj", "dbf", "shx"],
                    "optional_ext": ["xml", "sld", "cpg", "cst"],
                }
            ],
            "actions": list(self.TASKS.keys()),
            "type": "vector",
        }

    @staticmethod
    def can_do(action) -> bool:
        """
        Evaluate if the handler can take care of a specific action.
        Each action (import/copy/etc...) can define different step so
        the Handler must be ready to handle them. If is not in the actual
        flow the already in place flow is followd
        """
        return action in ShapeFileHandler.TASKS

    @staticmethod
    def can_handle(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        base = _data.get("base_file")
        if not base:
            return False
        ext = base.split(".")[-1] if isinstance(base, str) else base.name.split(".")[-1]
        return ext in ["shp"] and BaseVectorFileHandler.can_handle(_data)

    @staticmethod
    def has_serializer(data) -> bool:
        _base = data.get("base_file")
        if not _base:
            return False
        if data.get("action") == ira.UPSERT.value:
            return False
        if _base.endswith("shp") if isinstance(_base, str) else _base.name.endswith("shp"):
            is_overwrite_flow = data.get("overwrite_existing_layer", False)
            if isinstance(is_overwrite_flow, str):
                is_overwrite_flow = ast.literal_eval(is_overwrite_flow.title())
            return OverwriteShapeFileSerializer if is_overwrite_flow else ShapeFileSerializer
        return False

    @staticmethod
    def extract_params_from_data(_data, action=None):
        """
        Remove from the _data the params that needs to save into the executionRequest object
        all the other are returned
        """
        if action == exa.COPY.value:
            title = json.loads(_data.get("defaults"))
            return {"title": title.pop("title"), "store_spatial_file": True}, _data

        additional_params = {
            "skip_existing_layers": _data.pop("skip_existing_layers", "False"),
            "overwrite_existing_layer": _data.pop("overwrite_existing_layer", False),
            "resource_pk": _data.pop("resource_pk", None),
            "store_spatial_file": _data.pop("store_spatial_files", "True"),
            "action": _data.pop("action", "upload"),
            "upsert_key": _data.pop("upsert_key", None),
        }

        return additional_params, _data

    @staticmethod
    def is_valid(files, user, **kwargs):
        """
        Define basic validation steps:
        """
        # getting the upload limit validation
        upload_validator = UploadLimitValidator(user)
        upload_validator.validate_parallelism_limit_per_user()

        _file = files.get("base_file")
        if not _file:
            raise InvalidShapeFileException("base file is not provided")

        _filename = Path(_file).stem

        _shp_ext_needed = ShapeFileHandler._get_ext_needed()

        """
        Check if the ext required for the shape file are available in the files uploaded
        by the user
        """
        is_valid = all(
            map(
                lambda x: any(
                    (
                        _ext.endswith(f"{_filename}.{x}")
                        if isinstance(_ext, str)
                        else _ext.name.endswith(f"{_filename}.{x}")
                    )
                    for _ext in files.values()
                ),
                _shp_ext_needed,
            )
        )
        if not is_valid:
            raise InvalidShapeFileException(
                detail=f"Some file is missing files with the same name and with the following extension are required: {_shp_ext_needed}"
            )

        return True

    @staticmethod
    def _get_ext_needed():
        for x in get_supported_datasets_file_types():
            if x["id"] == "shp":
                for item in x["formats"][0]["required_ext"]:
                    yield item

    def get_ogr2ogr_driver(self):
        return ogr.GetDriverByName("ESRI Shapefile")

    @staticmethod
    def create_ogr2ogr_command(files, original_name, ovverwrite_layer, alternate, **kwargs):
        """
        Define the ogr2ogr command to be executed.
        This is a default command that is needed to import a vector file
        """
        base_command = BaseVectorFileHandler.create_ogr2ogr_command(files, original_name, ovverwrite_layer, alternate)
        additional_options = []
        encoding = ShapeFileHandler._get_encoding(files)

        if encoding:
            additional_options.append(f"--config SHAPE_ENCODING {encoding}")

        return (
            f"{base_command} -lco precision=no -lco GEOMETRY_NAME={BaseVectorFileHandler().default_geometry_column_name} "
            + " ".join(additional_options)
        )

    @staticmethod
    def _get_encoding(files):
        if files.get("cpg_file"):
            # prefer cpg file which is handled by gdal
            return None

        encoding = None
        if files.get("cst_file"):
            # GeoServer exports cst-file
            encoding_file = files.get("cst_file")
            with open(encoding_file, "r") as f:
                encoding = f.read()
            try:
                codecs.lookup(encoding)
            except LookupError as e:
                encoding = None
                logger.error(f"Will ignore invalid encoding: {e}")
        return encoding

    def promote_to_multi(self, geometry_name):
        """
        If needed change the name of the geometry, by promoting it to Multi
        example if is Point -> MultiPoint
        Needed for the shapefiles
        Later this is used to map the geometry coming from ogr2ogr with a django class
        """
        if "Multi" not in geometry_name and "Point" not in geometry_name and "3D" not in geometry_name:
            return f"Multi {geometry_name.title()}"
        return geometry_name

    def promote_geom_to_multi(self, geom):
        """
        Convert the GetGeometryType object into Multi
        example if is Point -> MultiPoint
        Needed for the shapefiles
        """
        match geom.GetGeometryType():
            case ogr.wkbMultiLineString | ogr.wkbMultiPolygon:
                # if is already multi, we dont need to do anything
                return geom
            case ogr.wkbLineString:
                new_multi_geom = ogr.Geometry(ogr.wkbMultiLineString)
                new_multi_geom.AddGeometry(geom)
                return new_multi_geom
            case ogr.wkbPolygon:
                new_multi_geom = ogr.Geometry(ogr.wkbMultiPolygon)
                new_multi_geom.AddGeometry(geom)
                return new_multi_geom
            case _:
                # we dont convert points
                return geom
