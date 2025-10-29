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

from celery import chord, group
from geonode.upload.api.exceptions import ImportException
from geonode.upload.handlers.base import BaseHandler
from geonode.upload.handlers.empty_dataset.utils import (
    add_attributes_to_xml,
    apply_restrictions_to_xml,
    should_apply_restrictions,
    validate_attributes,
    base_xml,
)
from geonode.upload.handlers.utils import EMPTY_DATASET_SUPPORTED_TYPES, GEOM_TYPE_MAPPING, drop_dynamic_model_schema
from geonode.upload.orchestrator import orchestrator
from geonode.upload.handlers.common.vector import BaseVectorFileHandler, import_next_step
from geonode.upload.handlers.empty_dataset.serializer import EmptyDatasetSerializer
from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.upload.utils import DEFAULT_PK_COLUMN_NAME


logger = logging.getLogger("importer")

BBOX = [-180, -90, 180, 90]


class EmptyDatasetHandler(BaseVectorFileHandler):
    """
    Handler to import GeoJson files into GeoNode data db
    It must provide the task_lists required to comple the upload
    """

    # we dont need the upload action for the empty dataset
    TASKS = BaseVectorFileHandler.TASKS.copy()
    TASKS.pop(exa.UPLOAD.value)
    # but we need the create one via the UI
    TASKS.update(
        {
            exa.CREATE.value: (
                "start_import",
                "geonode.upload.import_resource",
                "geonode.upload.publish_resource",
                "geonode.upload.create_geonode_resource",
            )
        }
    )

    @property
    def supported_file_extension_config(self):
        return {}

    @property
    def default_geometry_column_name(self):
        return "geom"

    @staticmethod
    def can_handle(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        base = _data.get("base_file")
        if not base and _data.get("is_empty"):
            return True

        return False

    @staticmethod
    def can_do(action) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        return action in EmptyDatasetHandler.TASKS

    @staticmethod
    def has_serializer(_data) -> bool:
        """
        This endpoint should return (if set) the custom serializer used in the API
        to validate the input resource
        """
        if _data.get("attributes", None) is not None and _data.get("action") in EmptyDatasetHandler.TASKS:
            return EmptyDatasetSerializer

    @staticmethod
    def is_valid(files, user, **kwargs):
        # improve the logic once the structure is defined
        exec_obj = orchestrator.get_execution_object(exec_id=kwargs.get("execution_id"))
        params = exec_obj.input_params
        if "geom" in params and "title" in params and "attributes" in params and params.get("is_empty"):
            return True
        else:
            raise ImportException("The payload provided is not valid for an empty dataset")

    @staticmethod
    def extract_params_from_data(_data, action=None):
        """
        Remove from the _data the params that needs to save into the executionRequest object
        all the other are returned
        """
        return {
            "title": _data.pop("title", None),
            "geom": _data.pop("geom", None),
            "attributes": _data.pop("attributes", None),
            "action": _data.pop("action", None),
            "is_empty": _data.pop("is_empty", True),
            "is_dynamic_model_managed": _data.pop("is_dynamic_model_managed", True),
        }, _data

    def import_resource(self, files, execution_id, **kwargs):
        # define the dynamic model
        try:

            logger.info("Total number of layers available: 1")
            exec_obj = orchestrator.get_execution_object(execution_id)

            _input = {**exec_obj.input_params, **{"total_layers": 1}}
            orchestrator.update_execution_request_status(execution_id=str(execution_id), input_params=_input)
            dynamic_model = None

            input_params = exec_obj.input_params

            layer_name = self.fixup_name(input_params["title"])
            task_name = "geonode.upload.import_resource"

            (
                dynamic_model,
                alternate,
                celery_group,
            ) = self.setup_dynamic_model(
                input_params.get("title"),
                execution_id=execution_id,
                should_be_overwritten=False,
                username=exec_obj.user,
            )

            group_to_call = group(
                celery_group.set(link_error=["dynamic_model_error_callback"]),
                # ogr_res.set(link_error=["dynamic_model_error_callback"]),
            )
            # prepare the async chord workflow with the on_success and on_fail methods
            workflow = chord(group_to_call)(  # noqa
                import_next_step.s(
                    execution_id,
                    str(self),  # passing the handler module path
                    task_name,
                    layer_name,
                    alternate,
                    **kwargs,
                )
            )
            return [layer_name], [alternate], execution_id
        except Exception as e:
            logger.error(e)
            if dynamic_model:
                """
                In case of fail, we want to delete the dynamic_model schema and his field
                to keep the DB in a consistent state
                """
                drop_dynamic_model_schema(dynamic_model)
            raise e

    def _get_type(self, _type):
        return EMPTY_DATASET_SUPPORTED_TYPES.get(_type)

    def _define_dynamic_layer_schema(self, layer, **kwargs):
        exec_obj = orchestrator.get_execution_object(kwargs.get("execution_id"))
        input_params = exec_obj.input_params
        layer_schema = [
            {
                "name": self.fixup_name(name),
                "class_name": self._get_type(options["type"]),
                "null": options.get("nillable", False),
            }
            for name, options in input_params["attributes"].items()
        ]
        layer_schema += [
            {
                "name": self.default_geometry_column_name,
                "class_name": GEOM_TYPE_MAPPING.get(
                    self.promote_to_multi(input_params.get("geom", self.default_geometry_column_name))
                ),
                "dim": 2,
                "authority": "EPSG:4326",
            }
        ]
        layer_schema += [
            {
                "name": DEFAULT_PK_COLUMN_NAME,
                "class_name": "django.db.models.BigAutoField",
                "null": False,
                "primary_key": True,
            }
        ]
        return layer_schema

    def extract_resource_to_publish(self, files, action, layer_name, alternate, **kwargs):
        return [{"name": alternate or layer_name, "crs": "EPSG:4326", "exec_id": kwargs.get("exec_id")}]

    def handle_thumbnail(self, saved_dataset, _exec):
        """
        we can skip the thumbnail creation for an empty dataset
        """
        pass

    @staticmethod
    def publish_resources(resources, catalog, store, workspace):
        # creating the gs resource as always
        BaseVectorFileHandler().publish_resources(resources, catalog, store, workspace)
        res = resources[0]
        exec_obj = orchestrator.get_execution_object(exec_id=res.get("exec_id"))
        attributes = exec_obj.input_params.get("attributes")
        normalized_attributes = {BaseHandler().fixup_name(key): value for key, value in attributes.items()}
        validate_attributes(normalized_attributes)

        xml = add_attributes_to_xml(
            {
                **{DEFAULT_PK_COLUMN_NAME: {"type": "integer", "nillable": False}},
                **normalized_attributes,
                # include geometry as an available attribute
                "geom": {"type": exec_obj.input_params.get("geom"), "nillable": False},
            },
            base_xml.format(name=res.get("name")),
        )

        if should_apply_restrictions(normalized_attributes):
            xml = apply_restrictions_to_xml(normalized_attributes, xml)

        url = (
            f"{catalog.service_url}/workspaces/{workspace.name}/datastores/{store.name}/featuretypes/{res.get('name')}"
        )

        req = catalog.http_request(url, data=xml, method="PUT", headers={"Content-Type": "application/xml"})
        req.raise_for_status()
        return True
