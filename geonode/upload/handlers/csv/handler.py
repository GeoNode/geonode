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

from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.upload.api.exceptions import UploadParallelismLimitException
from geonode.upload.utils import UploadLimitValidator
from geonode.upload.celery_tasks import create_dynamic_structure
from geonode.upload.handlers.csv.exceptions import InvalidCSVException
from osgeo import ogr
from celery import group
from geonode.base.models import ResourceBase
from dynamic_models.models import ModelSchema
from geonode.upload.handlers.common.vector import BaseVectorFileHandler
from geonode.upload.handlers.utils import GEOM_TYPE_MAPPING

logger = logging.getLogger("importer")


class CSVFileHandler(BaseVectorFileHandler):
    """
    Handler to import CSV files into GeoNode data db
    It must provide the task_lists required to comple the upload
    """

    possible_geometry_column_name = ["geom", "geometry", "wkt_geom", "the_geom"]
    possible_lat_column = ["latitude", "lat", "y"]
    possible_long_column = ["longitude", "long", "x"]
    possible_latlong_column = possible_lat_column + possible_long_column

    @property
    def supported_file_extension_config(self):
        return {
            "id": "csv",
            "formats": [
                {
                    "label": "CSV",
                    "required_ext": ["csv"],
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
            base.lower().endswith(".csv") if isinstance(base, str) else base.name.lower().endswith(".csv")
        ) and BaseVectorFileHandler.can_handle(_data)

    @staticmethod
    def is_valid(files, user, **kwargs):
        BaseVectorFileHandler.is_valid(files, user)
        # getting the upload limit validation
        upload_validator = UploadLimitValidator(user)
        upload_validator.validate_parallelism_limit_per_user()
        actual_upload = upload_validator._get_parallel_uploads_count()
        max_upload = upload_validator._get_max_parallel_uploads()

        layers = CSVFileHandler().get_ogr2ogr_driver().Open(files.get("base_file"))

        if not layers:
            raise InvalidCSVException("The CSV provided is invalid, no layers found")

        layers_count = len(layers)

        if layers_count >= max_upload:
            raise UploadParallelismLimitException(
                detail=f"The number of layers in the CSV {layers_count} is greater than "
                f"the max parallel upload permitted: {max_upload} "
                f"please upload a smaller file"
            )
        elif layers_count + actual_upload >= max_upload:
            raise UploadParallelismLimitException(
                detail=f"With the provided CSV, the number of max parallel upload will exceed the limit of {max_upload}"
            )

        schema_keys = [x.name.lower() for layer in layers for x in layer.schema]
        geom_is_in_schema = any(x in schema_keys for x in CSVFileHandler().possible_geometry_column_name)
        has_lat = any(x in CSVFileHandler().possible_lat_column for x in schema_keys)
        has_long = any(x in CSVFileHandler().possible_long_column for x in schema_keys)

        fields = CSVFileHandler().possible_geometry_column_name + CSVFileHandler().possible_latlong_column
        if has_lat and not has_long:
            raise InvalidCSVException(
                f"Longitude is missing. Supported names: {', '.join(CSVFileHandler().possible_long_column)}"
            )

        if not has_lat and has_long:
            raise InvalidCSVException(
                f"Latitude is missing. Supported names: {', '.join(CSVFileHandler().possible_lat_column)}"
            )

        if not geom_is_in_schema and not has_lat and not has_long:
            raise InvalidCSVException(f"Not enough geometry field are set. The possibilities are: {','.join(fields)}")

        return True

    def get_ogr2ogr_driver(self):
        return ogr.GetDriverByName("CSV")

    @staticmethod
    def create_ogr2ogr_command(files, original_name, ovverwrite_layer, alternate):
        """
        Define the ogr2ogr command to be executed.
        This is a default command that is needed to import a vector file
        """
        base_command = BaseVectorFileHandler.create_ogr2ogr_command(files, original_name, ovverwrite_layer, alternate)
        additional_option = ' -oo "GEOM_POSSIBLE_NAMES=geom*,the_geom*,wkt_geom" -oo "X_POSSIBLE_NAMES=x,long*" -oo "Y_POSSIBLE_NAMES=y,lat*"'
        return (
            f"{base_command } -oo KEEP_GEOM_COLUMNS=NO -lco GEOMETRY_NAME={BaseVectorFileHandler().default_geometry_column_name} "
            + additional_option
        )

    def create_dynamic_model_fields(
        self,
        layer: str,
        dynamic_model_schema: ModelSchema,
        overwrite: bool,
        execution_id: str,
        layer_name: str,
    ):
        # retrieving the field schema from ogr2ogr and converting the type to Django Types
        layer_schema = [{"name": x.name.lower(), "class_name": self._get_type(x), "null": True} for x in layer.schema]
        if (
            layer.GetGeometryColumn()
            or self.default_geometry_column_name
            and ogr.GeometryTypeToName(layer.GetGeomType()) not in ["Geometry Collection", "Unknown (any)"]
        ):
            # the geometry colum is not returned rom the layer.schema, so we need to extract it manually
            # checking if the geometry has been wrogly read as string
            schema_keys = [x["name"] for x in layer_schema]
            geom_is_in_schema = (x in schema_keys for x in self.possible_geometry_column_name)
            if any(geom_is_in_schema) and layer.GetGeomType() == 100:  # 100 means None so Geometry not found
                field_name = [x for x in self.possible_geometry_column_name if x in schema_keys][0]
                index = layer.GetFeature(1).keys().index(field_name)
                geom = [x for x in layer.GetFeature(1)][index]
                class_name = GEOM_TYPE_MAPPING.get(self.promote_to_multi(geom.split("(")[0].replace(" ", "").title()))
                layer_schema = [x for x in layer_schema if field_name not in x["name"]]
            elif any(x in self.possible_latlong_column for x in schema_keys):
                class_name = GEOM_TYPE_MAPPING.get(self.promote_to_multi("Point"))
            else:
                class_name = GEOM_TYPE_MAPPING.get(self.promote_to_multi(ogr.GeometryTypeToName(layer.GetGeomType())))

            layer_schema += [
                {
                    "name": layer.GetGeometryColumn() or self.default_geometry_column_name,
                    "class_name": class_name,
                    "dim": (2 if not ogr.GeometryTypeToName(layer.GetGeomType()).lower().startswith("3d") else 3),
                }
            ]

        # ones we have the schema, here we create a list of chunked value
        # so the async task will handle max of 30 field per task
        list_chunked = [layer_schema[i : i + 30] for i in range(0, len(layer_schema), 30)]  # noqa

        # definition of the celery group needed to run the async workflow.
        # in this way each task of the group will handle only 30 field
        celery_group = group(
            create_dynamic_structure.s(execution_id, schema, dynamic_model_schema.id, overwrite, layer_name)
            for schema in list_chunked
        )

        return dynamic_model_schema, celery_group

    def extract_resource_to_publish(self, files, action, layer_name, alternate, **kwargs):
        if action == exa.COPY.value:
            return [
                {
                    "name": alternate,
                    "crs": ResourceBase.objects.filter(alternate__istartswith=layer_name).first().srid,
                }
            ]

        layers = self.get_ogr2ogr_driver().Open(files.get("base_file"), 0)
        if not layers:
            return []
        return [
            {
                "name": alternate or layer_name,
                "crs": (self.identify_authority(_l)),
            }
            for _l in layers
            if self.fixup_name(_l.GetName()) == layer_name
        ]

    def identify_authority(self, layer):
        try:
            authority_code = super().identify_authority(layer=layer)
            return authority_code
        except Exception:
            return "EPSG:4326"
