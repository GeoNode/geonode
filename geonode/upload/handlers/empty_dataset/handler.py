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

import xml.etree.ElementTree as ET
from celery import chord, group
from geonode.upload.api.exceptions import ImportException
from geonode.upload.handlers.utils import EMPTY_DATASET_SUPPORTED_TYPES, GEOM_TYPE_MAPPING, drop_dynamic_model_schema
from geonode.upload.orchestrator import orchestrator
from geonode.upload.handlers.common.vector import BaseVectorFileHandler, import_next_step
from osgeo import ogr
from geonode.upload.handlers.empty_dataset.serializer import EmptyDatasetSerializer
from geonode.resource.enumerator import ExecutionRequestAction as exa


logger = logging.getLogger("importer")

BBOX = [-180, -90, 180, 90]
DATA_QUALITY_MESSAGE = "Created with GeoNode"
ATTRIBUTE_TYPE_MAP = {
    "string": "java.lang.String",
    "float": "java.lang.Float",
    "integer": "java.lang.Integer",
    "date": "java.sql.Date",
    "Point": "com.vividsolutions.jts.geom.Point",
    "LineString": "com.vividsolutions.jts.geom.LineString",
    "Polygon": "com.vividsolutions.jts.geom.Polygon",
}
RESTRICTION_OPTIONS_TYPE_MAP = {"string": "string", "float": "float", "integer": "int"}


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

    @staticmethod
    def can_handle(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        base = _data.get("base_file")
        if not base and _data.get("is_empty"):
            # TODO improve the logic when the payload is decided
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
        if _data.get("attributes"):
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

    def get_ogr2ogr_driver(self):
        return ogr.GetDriverByName("OGR_VRT")

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

    def _define_dynamic_layer_scema(self, layer, **kwargs):
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
            {"name": "fid", "class_name": "django.db.models.BigAutoField", "null": False, "primary_key": True}
        ]
        return layer_schema

    @staticmethod
    def create_ogr2ogr_command(files, original_name, ovverwrite_layer, alternate, **kwargs):
        """
        Define the ogr2ogr command to be executed.
        This is a default command that is needed to import a vector file
        """
        converter = {"string": "VARCHAR(250)", "float": "DOUBLE PRECISION", "int": "NUMERIC", "date": "DATE"}
        # vsizero will let ogr2ogr ignore the input file
        exec_obj = orchestrator.get_execution_object(exec_id=kwargs.get("execution_id"))
        column_string = ""
        base = BaseVectorFileHandler.create_ogr2ogr_command(
            {"base_file": "/vsizero/"}, original_name, ovverwrite_layer, alternate
        )
        # name:VARCHAR(50),value:NUMERIC,timestamp:TIMESTAMP
        for element in exec_obj.input_params.get("attributes"):
            column_string += f"{element['name']}:{converter.get(element['type'])},"
        return base + f'-lco "GEOMETRY_TYPE=POINT" -lco "FID=ogc_fid" -lco "COLUMN_TYPES={column_string}"'

    def extract_resource_to_publish(self, files, action, layer_name, alternate, **kwargs):
        return [{"name": alternate or layer_name, "crs": "EPSG:4326", "exec_id": kwargs.get("exec_id")}]

    @staticmethod
    def publish_resources(resources, catalog, store, workspace):
        # result = BaseVectorFileHandler().publish_resources(resources, catalog, store, workspace)
        res = resources[0]
        exec_obj = orchestrator.get_execution_object(exec_id=res.get("exec_id"))
        attributes = exec_obj.input_params.get("attributes")

        # publishing attributes in GeoServer
        def validate_attributes(attributes_dict):
            for name in attributes_dict:
                info = attributes_dict[name]
                attr_type = info.get("type")
                attr_options = info.get("options")
                attr_range = info.get("range")
                if len(name) == 0:
                    msg = f"You must provide an attribute name for attribute of type {attr_type}"
                    logger.error(msg)
                    raise ImportException(msg)
                if not ATTRIBUTE_TYPE_MAP.get(attr_type):
                    msg = f"{attr_type} is not a valid type for attribute {name}"
                    logger.error(msg)
                    raise ImportException(msg)
                if attr_type == "date" and attr_options:
                    msg = f"{attr_type} does not support options restriction"
                    logger.error(msg)
                    raise ImportException(msg)
                if attr_type in ["date", "string"] and attr_range:
                    msg = f"{attr_type} does not support range restriction"
                    logger.error(msg)
                    raise ImportException(msg)
            return True

        def should_apply_restrictions(attributes_dict):
            for name in attributes_dict:
                info = attributes_dict[name]
                attr_options = info.get("options")
                attr_range = info.get("range")
                if attr_options or attr_range:
                    return True
            return False

        def add_attributes_to_xml(attributes_dict, xml):
            root = ET.fromstring(xml)
            attributes_tag = root.find("attributes")
            for name in attributes_dict:
                info = attributes_dict[name]
                attr_name = name
                attr_type = ATTRIBUTE_TYPE_MAP.get(info.get("type"))
                attr_nillable = "false"
                if info.get("nillable"):
                    attr_nillable = "true"
                attribute_tag = ET.SubElement(attributes_tag, "attribute")
                ET.SubElement(attribute_tag, "name").text = f"{attr_name}"
                ET.SubElement(attribute_tag, "binding").text = f"{attr_type}"
                ET.SubElement(attribute_tag, "nillable").text = f"{attr_nillable}"
            return ET.tostring(root)

        def apply_restrictions_to_xml(attributes_dict, xml):
            root = ET.fromstring(xml)
            attributes_tag = root.find("attributes")
            for attribute in attributes_tag.findall("attribute"):
                name = attribute.find("name").text
                info = attributes_dict.get(name, None)
                if info:
                    restrictions_range = info.get("range")
                    if restrictions_range:
                        min_restrictions_range = restrictions_range.get("min", None)
                        max_restrictions_range = restrictions_range.get("max", None)
                        range_tag = ET.SubElement(attribute, "range")
                        if min_restrictions_range is not None:
                            ET.SubElement(range_tag, "min").text = f"{min_restrictions_range}"
                        if max_restrictions_range is not None:
                            ET.SubElement(range_tag, "max").text = f"{max_restrictions_range}"
                    restrictions_options = info.get("options")
                    if restrictions_options:
                        options_tag = ET.SubElement(attribute, "options")
                        for option in restrictions_options:
                            ET.SubElement(options_tag, RESTRICTION_OPTIONS_TYPE_MAP.get(info.get("type"))).text = (
                                f"{option}"
                            )
            return ET.tostring(root)

        base_xml = (
            "<featureType>"
            f"<name>{res.get('name')}</name>"
            f"<nativeName>{res.get('name')}</nativeName>"
            f"<title>{res.get('name')}</title>"
            "<srs>EPSG:4326</srs>"
            f"<latLonBoundingBox><minx>{BBOX[0]}</minx><maxx>{BBOX[2]}</maxx><miny>{BBOX[1]}</miny><maxy>{BBOX[3]}</maxy>"
            "<crs>EPSG:4326</crs></latLonBoundingBox>"
            "<attributes></attributes>"
            "</featureType>"
        )

        validate_attributes(attributes)

        xml = add_attributes_to_xml(
            {
                **attributes,
                # include geometry as an available attribute
                "geom": {"type": exec_obj.input_params.get("geom"), "nillable": False},
            },
            base_xml,
        )

        if should_apply_restrictions(attributes):
            xml = apply_restrictions_to_xml(attributes, xml)

        url = f"{catalog.service_url}/workspaces/{workspace.name}/datastores/{store.name}/featuretypes"
        req = catalog.http_request(url, data=xml, method="POST", headers={"Content-Type": "application/xml"})
        if req.status_code != 201:
            logger.error(f"Request status code was: {req.status_code}")
            logger.error(f"Response was: {req.text}")
            raise Exception(f"Dataset could not be created in GeoServer {req.text}")

        return True
