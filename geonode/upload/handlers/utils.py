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
import hashlib

from django.contrib.auth import get_user_model
from geonode.base.models import ResourceBase
from geonode.resource.models import ExecutionRequest
import logging
from dynamic_models.schema import ModelSchemaEditor
from django.utils.module_loading import import_string
from uuid import UUID

from geonode.upload.publisher import DataPublisher

logger = logging.getLogger("importer")


STANDARD_TYPE_MAPPING = {
    "Integer64": "django.db.models.IntegerField",
    "Integer": "django.db.models.IntegerField",
    "DateTime": "django.db.models.DateTimeField",
    "Date": "django.db.models.DateField",
    "Real": "django.db.models.FloatField",
    "String": "django.db.models.CharField",
    "StringList": "django.db.models.fields.json.JSONField",
}

GEOM_TYPE_MAPPING = {
    "Line String": "django.contrib.gis.db.models.fields.LineStringField",
    "Linestring": "django.contrib.gis.db.models.fields.LineStringField",
    "3D Line String": "django.contrib.gis.db.models.fields.LineStringField",
    "Multi Line String": "django.contrib.gis.db.models.fields.MultiLineStringField",
    "Multilinestring": "django.contrib.gis.db.models.fields.MultiLineStringField",
    "3D Multi Line String": "django.contrib.gis.db.models.fields.MultiLineStringField",
    "Point": "django.contrib.gis.db.models.fields.PointField",
    "3D Point": "django.contrib.gis.db.models.fields.PointField",
    "Multi Point": "django.contrib.gis.db.models.fields.MultiPointField",
    "Multipoint": "django.contrib.gis.db.models.fields.MultiPointField",
    "Polygon": "django.contrib.gis.db.models.fields.PolygonField",
    "3D Polygon": "django.contrib.gis.db.models.fields.PolygonField",
    "3D Multi Point": "django.contrib.gis.db.models.fields.MultiPointField",
    "Multi Polygon": "django.contrib.gis.db.models.fields.MultiPolygonField",
    "Multipolygon": "django.contrib.gis.db.models.fields.MultiPolygonField",
    "3D Multi Polygon": "django.contrib.gis.db.models.fields.MultiPolygonField",
}


def should_be_imported(layer: str, user: get_user_model(), **kwargs) -> bool:  # type: ignore
    """
    If layer_name + user (without the addition of any execution id)
    already exists, will apply one of the rule available:
    - skip_existing_layer: means that if already exists will be skept
    - ovverwrite_layer: means that if already exists will be overridden
        - the dynamic model should be recreated
        - ogr2ogr should overwrite the layer
        - the publisher should republish the resource
        - geonode should update it
    """
    workspace = DataPublisher(None).workspace
    exists = ResourceBase.objects.filter(alternate=f"{workspace.name}:{layer}", owner=user).exists()

    if exists and kwargs.get("skip_existing_layer", False):
        return False

    return True


def create_alternate(layer_name, execution_id):
    """
    Utility to generate the expected alternate for the resource
    is alternate = layer_name_ + md5(layer_name + uuid)
    """
    _hash = hashlib.md5(f"{layer_name}_{execution_id}".encode("utf-8")).hexdigest()
    alternate = f"{layer_name}_{_hash}"
    if len(alternate) >= 63:  # 63 is the max table lengh in postgres to stay safe, we cut at 12
        return f"{layer_name[:50]}{_hash[:12]}"
    return alternate


def drop_dynamic_model_schema(schema_model):
    if schema_model:
        schema = ModelSchemaEditor(initial_model=schema_model.name, db_name="datastore")
        try:
            schema_model.delete()
            schema.drop_table(schema_model.as_model())
        except Exception as e:
            logger.warning(e.args[0])


def get_uuid(_list):
    for el in _list:
        try:
            UUID(el)
            return el
        except Exception:
            continue


def evaluate_error(celery_task, exc, task_id, args, kwargs, einfo):
    """
    Main error function used by the task for the "on_failure" function
    """
    from geonode.upload.celery_tasks import orchestrator

    exec_id = orchestrator.get_execution_object(exec_id=get_uuid(args))
    output_params = exec_id.output_params.copy()

    if exec_id.status == ExecutionRequest.STATUS_FAILED:
        logger.info("Execution is already in status FAILED")
        return

    logger.error(f"Task FAILED with ID: {str(exec_id.exec_id)}, reason: {exc}")

    handler = import_string(exec_id.input_params.get("handler_module_path"))

    # creting the log message
    _log = handler.create_error_log(exc, celery_task.name, *args)

    if output_params.get("errors"):
        output_params.get("errors").append(_log)
        output_params.get("failed_layers", []).append(args[-1] if args else [])
        failed = list(set(output_params.get("failed_layers", [])))
        output_params["failed_layers"] = failed
    else:
        output_params = {"errors": [_log], "failed_layers": [args[-1]]}

    celery_task.update_state(
        task_id=task_id,
        state="FAILURE",
        meta={"exec_id": str(exec_id.exec_id), "reason": _log},
    )
    orchestrator.update_execution_request_status(execution_id=str(exec_id.exec_id), output_params=output_params)

    orchestrator.evaluate_execution_progress(
        get_uuid(args), _log=str(exc.detail if hasattr(exc, "detail") else exc.args[0])
    )
