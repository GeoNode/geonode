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
import json
import logging
import os
from pathlib import Path
import math
from geonode.layers.models import Dataset
from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.upload.utils import UploadLimitValidator
from geonode.upload.handlers.tiles3d.utils import box_to_wgs84, sphere_to_wgs84
from geonode.upload.orchestrator import orchestrator
from geonode.upload.celery_tasks import import_orchestrator
from geonode.upload.handlers.common.vector import BaseVectorFileHandler
from geonode.upload.handlers.utils import create_alternate, should_be_imported
from geonode.upload.utils import ImporterRequestAction as ira
from geonode.base.models import ResourceBase
from geonode.upload.handlers.tiles3d.exceptions import Invalid3DTilesException

logger = logging.getLogger("importer")


class Tiles3DFileHandler(BaseVectorFileHandler):
    """
    Handler to import 3Dtiles files into GeoNode data db
    It must provide the task_lists required to comple the upload
    """

    TASKS = {
        exa.UPLOAD.value: (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.create_geonode_resource",
        ),
        exa.COPY.value: (
            "start_copy",
            "geonode.upload.copy_geonode_resource",
        ),
        ira.ROLLBACK.value: (
            "start_rollback",
            "geonode.upload.rollback",
        ),
    }

    @property
    def supported_file_extension_config(self):
        return {
            "id": "3dtiles",
            "formats": [
                {
                    "label": "3D Tiles",
                    "required_ext": ["zip"],
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
        try:
            base = _data.get("base_file")
            if not base:
                return False
            ext = base.split(".")[-1] if isinstance(base, str) else base.name.split(".")[-1]
            if ext in ["json"] and Tiles3DFileHandler.is_3dtiles_json(base):
                return True
        except Exception:
            return False
        return False

    @staticmethod
    def is_valid(files, user, **kwargs):
        """
        Define basic validation steps:
        """
        # calling base validation checks
        BaseVectorFileHandler.is_valid(files, user)
        # getting the upload limit validation
        upload_validator = UploadLimitValidator(user)
        upload_validator.validate_parallelism_limit_per_user()

        _file = files.get("base_file")
        if not _file:
            raise Invalid3DTilesException("base file is not provided")

        filename = os.path.basename(_file)

        if len(filename.split(".")) > 2:
            # means that there is a dot other than the one needed for the extension
            # if we keep it ogr2ogr raise an error, better to remove it
            raise Invalid3DTilesException("Please remove the additional dots in the filename")

        try:
            _file = Tiles3DFileHandler.is_3dtiles_json(_file)

            Tiles3DFileHandler.validate_3dtile_payload(payload=_file)

        except Exception as e:
            raise Invalid3DTilesException(e)

        return True

    @staticmethod
    def is_3dtiles_json(_file):
        with open(_file, "r") as _readed_file:
            _file = json.loads(_readed_file.read())
            # required key described in the specification of 3dtiles
            # https://docs.ogc.org/cs/22-025r4/22-025r4.html#toc92
        is_valid = all(key in _file.keys() for key in ("asset", "geometricError", "root"))

        if not is_valid:
            raise Invalid3DTilesException(
                "The provided 3DTiles is not valid, some of the mandatory keys are missing. Mandatory keys are: 'asset', 'geometricError', 'root'"
            )

        return _file

    @staticmethod
    def validate_3dtile_payload(payload):
        # if the keys are there, let's check if the mandatory child are there too
        asset = payload.get("asset", {}).get("version", None)
        if not asset:
            raise Invalid3DTilesException("The mandatory 'version' for the key 'asset' is missing")
        volume = payload.get("root", {}).get("boundingVolume", None)
        if not volume:
            raise Invalid3DTilesException("The mandatory 'boundingVolume' for the key 'root' is missing")

        error = payload.get("geometricError", None) or payload.get("root", {}).get("geometricError", None)
        if error is None:
            raise Invalid3DTilesException("The mandatory 'geometricError' for the key 'root' is missing")

    @staticmethod
    def extract_params_from_data(_data, action=None):
        """
        Remove from the _data the params that needs to save into the executionRequest object
        all the other are returned
        """
        if action == exa.COPY.value:
            title = json.loads(_data.get("defaults"))
            return {"title": title.pop("title"), "store_spatial_file": True}, _data

        return {
            "skip_existing_layers": _data.pop("skip_existing_layers", "False"),
            "store_spatial_file": _data.pop("store_spatial_files", "True"),
            "action": _data.pop("action", "upload"),
            "original_zip_name": _data.pop("original_zip_name", None),
            "overwrite_existing_layer": _data.pop("overwrite_existing_layer", False),
        }, _data

    def import_resource(self, files: dict, execution_id: str, **kwargs) -> str:
        logger.info("Total number of layers available: 1")

        _exec = self._get_execution_request_object(execution_id)

        _input = {**_exec.input_params, **{"total_layers": 1}}

        orchestrator.update_execution_request_status(execution_id=str(execution_id), input_params=_input)
        filename = _exec.input_params.get("original_zip_name") or Path(files.get("base_file")).stem
        # start looping on the layers available
        layer_name = self.fixup_name(filename)
        should_be_overwritten = _exec.input_params.get("overwrite_existing_layer")
        # should_be_imported check if the user+layername already exists or not
        if should_be_imported(
            layer_name,
            _exec.user,
            skip_existing_layer=_exec.input_params.get("skip_existing_layer"),
            overwrite_existing_layer=should_be_overwritten,
        ):

            user_datasets = ResourceBase.objects.filter(owner=_exec.user, alternate=layer_name)

            dataset_exists = user_datasets.exists()

            if dataset_exists and should_be_overwritten:
                layer_name, alternate = (
                    layer_name,
                    user_datasets.first().alternate.split(":")[-1],
                )
            elif not dataset_exists:
                alternate = layer_name
            else:
                alternate = create_alternate(layer_name, execution_id)

        import_orchestrator.apply_async(
            (
                files,
                execution_id,
                str(self),
                "geonode.upload.import_resource",
                layer_name,
                alternate,
                exa.UPLOAD.value,
            )
        )
        return layer_name, alternate, execution_id

    def create_geonode_resource(
        self,
        layer_name: str,
        alternate: str,
        execution_id: str,
        resource_type: Dataset = ...,
        asset=None,
    ):
        # we want just the tileset.json as location of the asset
        asset.location = [path for path in asset.location if path.endswith(".json")]
        asset.save()

        resource = super().create_geonode_resource(layer_name, alternate, execution_id, ResourceBase, asset)

        # fixing-up bbox for the 3dtile object
        js_file = None
        with open(asset.location[0]) as _file:
            js_file = json.loads(_file.read())

        if not js_file:
            return resource

        if self._has_region(js_file):
            resource = self.set_bbox_from_region(js_file, resource=resource)
        elif self._has_sphere(js_file):
            resource = self.set_bbox_from_boundingVolume_sphere(js_file, resource=resource)
        else:
            resource = self.set_bbox_from_boundingVolume(js_file, resource=resource)

        return resource

    def generate_resource_payload(self, layer_name, alternate, asset, _exec, workspace):
        return dict(
            resource_type="dataset",
            subtype="3dtiles",
            dirty_state=True,
            title=layer_name,
            owner=_exec.user,
            asset=asset,
            link_type="uploaded",
            extension="3dtiles",
            alternate=alternate,
        )

    def set_bbox_from_region(self, js_file, resource):
        # checking if the region is inside the json file
        region = js_file.get("root", {}).get("boundingVolume", {}).get("region", None)
        if not region:
            logger.info(f"No region found, the BBOX will not be updated for 3dtiles: {resource.title}")
            return resource
        west, south, east, nord = region[:4]
        # [xmin, ymin, xmax, ymax]
        resource.set_bbox_polygon(
            bbox=[
                math.degrees(west),
                math.degrees(south),
                math.degrees(east),
                math.degrees(nord),
            ],
            srid="EPSG:4326",
        )

        return resource

    def set_bbox_from_boundingVolume(self, js_file, resource):
        transform_raw = js_file.get("root", {}).get("transform", [])
        box_raw = js_file.get("root", {}).get("boundingVolume", {}).get("box", None)

        if not box_raw or (not transform_raw and not box_raw):
            # skipping if values are missing from the json file
            return resource

        result = box_to_wgs84(box_raw, transform_raw)
        # [xmin, ymin, xmax, ymax]
        resource.set_bbox_polygon(
            bbox=[
                result["minx"],
                result["miny"],
                result["maxx"],
                result["maxy"],
            ],
            srid="EPSG:4326",
        )

        return resource

    def set_bbox_from_boundingVolume_sphere(self, js_file, resource):
        transform_raw = js_file.get("root", {}).get("transform", [])
        sphere_raw = js_file.get("root", {}).get("boundingVolume", {}).get("sphere", None)

        if not sphere_raw or (not transform_raw and not sphere_raw):
            # skipping if values are missing from the json file
            return resource
        if not transform_raw and (sphere_raw[0], sphere_raw[1], sphere_raw[2]) == (0, 0, 0):
            return resource
        result = sphere_to_wgs84(sphere_raw, transform_raw)
        # [xmin, ymin, xmax, ymax]
        resource.set_bbox_polygon(
            bbox=[
                result["minx"],
                result["miny"],
                result["maxx"],
                result["maxy"],
            ],
            srid="EPSG:4326",
        )

        return resource

    def _has_region(self, js_file):
        return js_file.get("root", {}).get("boundingVolume", {}).get("region", None)

    def _has_sphere(self, js_file):
        return js_file.get("root", {}).get("boundingVolume", {}).get("sphere", None)
