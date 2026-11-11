#########################################################################
#
# Copyright (C) 2026 OSGeo
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
import typing

from django.conf import settings
from geoserver.catalog import FailedRequestError

from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.security.auth_registry import auth_handler_registry
from geonode.security.models import AuthConfig
from geonode.sources.models import DataItem
from geonode.upload.api.exceptions import ImportException
from geonode.upload.handlers.base import BaseHandler
from geonode.upload.publisher import DataPublisher
from geonode.upload.utils import ImporterRequestAction as ira

logger = logging.getLogger("importer")


class PostgresUploadHandler(BaseHandler):
    """
    Publishes a table of a PostgreSQL source connection in GeoServer, reading it in place: no data is copied
    and no GeoNode resource is created. Started by geonode.sources, never selected by the upload endpoint
    """

    TASKS = {
        exa.UPLOAD.value: (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.publish_resource",
        ),
        ira.ROLLBACK.value: (
            "start_rollback",
            "geonode.upload.rollback",
        ),
    }

    # set by extract_resource_to_publish, the publisher asks for the store right after on the same instance
    auth_config = None

    @staticmethod
    def store_name_of(auth_config_id) -> str:
        # one store per connection, shared by its tables
        return f"postgis_{auth_config_id}"

    def layer_name_of(self, table, auth_config_id) -> str:
        # the connection id keeps the name unique in the workspace
        return f"{self.fixup_name(table)}_{auth_config_id}"

    @staticmethod
    def is_valid(files, user, **kwargs):
        """The connection still exists and the table has a CRS, checked before anything reaches GeoServer"""
        # here to avoid circular import
        from geonode.upload.orchestrator import orchestrator

        _params = orchestrator.get_execution_object(kwargs["execution_id"]).input_params
        if not AuthConfig.objects.filter(pk=_params["auth_config_id"]).exists():
            raise ImportException("The connection of the table does not exist anymore.")
        if not any(_geom["srid"] for _geom in _params["details"]["geometries"]):
            raise ImportException("Only tables with a CRS can be published.")
        return True

    def import_resource(self, files: dict, execution_id: str, **kwargs):
        """Nothing is imported, the table is read in place: only the name of its layer is decided"""
        # here to avoid circular import
        from geonode.upload.celery_tasks import import_orchestrator
        from geonode.upload.orchestrator import orchestrator

        _exec = orchestrator.get_execution_object(execution_id)
        _name = self.layer_name_of(_exec.input_params["details"]["table"], _exec.input_params["auth_config_id"])
        # the data item and the rollback read it back from the execution
        orchestrator.update_execution_request_obj(_exec, {"input_params": {**_exec.input_params, "layer_name": _name}})
        import_orchestrator.apply_async(
            (files, execution_id, str(self), "geonode.upload.import_resource", _name, _name, exa.UPLOAD.value)
        )
        return _name, _name, execution_id

    def get_geoserver_store_name(self, default=None):
        return self.store_name_of(self.auth_config.pk), True

    def get_geoserver_store_parameters(self) -> typing.Dict:
        """GeoServer reads the tables in place, through the connection of the source"""
        _handler = auth_handler_registry.build(self.auth_config)
        return {
            "host": _handler.host,
            "port": str(_handler.port),
            "database": _handler.database,
            "user": _handler.username,
            "passwd": _handler.password,
            "schema": _handler.schema,
            "SSL mode": _handler.sslmode.upper().replace("-", "_"),
            # as the provider sessions: even a role allowed to write cannot change the source through WFS-T
            "Session startup SQL": "SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY",
            # not our database: no idle pool kept open on it
            "min connections": 1,
        }

    def extract_resource_to_publish(self, files, action, layer_name, alternate, **kwargs) -> typing.List[typing.Dict]:
        # here to avoid circular import
        from geonode.upload.orchestrator import orchestrator

        _params = orchestrator.get_execution_object(kwargs["exec_id"]).input_params
        self.auth_config = AuthConfig.objects.get(pk=_params["auth_config_id"])

        _table = _params["details"]["table"]
        _srids = [_geom["srid"] for _geom in _params["details"]["geometries"] if _geom["srid"]]
        if not _srids:
            # without a CRS GeoServer would publish a misconfigured layer
            return []
        return [{"name": alternate, "crs": f"EPSG:{_srids[0]}", "native_name": _table}]

    @staticmethod
    def publish_resources(resources, catalog, store, workspace):
        for _resource in resources:
            try:
                # the layer is renamed, the table keeps its own name
                catalog.publish_featuretype(
                    name=_resource["name"],
                    store=store,
                    native_crs=_resource["crs"],
                    native_name=_resource["native_name"],
                )
            except FailedRequestError as e:
                # a run that crashed after publishing left the layer: same store and name, it is this table's.
                # Not looked up first: the store catalog would cache the miss and the sanity check would not find it
                if "already exists" not in str(e):
                    raise
        return True

    @staticmethod
    def perform_last_step(execution_id):
        """The table is in GeoServer: only now it becomes a data item"""
        # here to avoid circular import
        from geonode.upload.orchestrator import orchestrator

        _exec = orchestrator.get_execution_object(execution_id)
        _params = _exec.input_params
        _item, _ = DataItem.objects.get_or_create(
            auth_config_id=_params["auth_config_id"],
            uri=_params["uri"],
            defaults={
                "source_provider": _params["source_provider"],
                "title": _params["title"],
                "details": _params["details"],
                "layer": f"{settings.DEFAULT_WORKSPACE}:{_params['layer_name']}",
                "created_by": _exec.user,
            },
        )
        _exec.output_params.update({"data_item": _item.pk})
        _exec.save()
        return _exec

    def _publish_resource_rollback(self, exec_id, instance_name=None, *args, **kwargs):
        """Remove the data item and the layer of the execution, never the table: the source is only read"""
        # here to avoid circular import
        from geonode.upload.orchestrator import orchestrator

        _exec = orchestrator.get_execution_object(exec_id)
        DataItem.objects.filter(pk=_exec.output_params.get("data_item")).delete()
        self.remove_layer(_exec.input_params["auth_config_id"], f"{settings.DEFAULT_WORKSPACE}:{instance_name}")

    def remove_layer(self, auth_config_id, layer):
        """Remove a layer of the connection from GeoServer, as workspace:name, and its store once no layer uses it"""
        _workspace, _name = layer.split(":", 1)
        _catalog = DataPublisher(None).cat
        _store = _catalog.get_store(self.store_name_of(auth_config_id), workspace=_workspace)
        if not _store:
            return
        _layer = _catalog.get_resource(_name, store=_store, workspace=_workspace)
        if _layer:
            _catalog.delete(_layer, recurse=True)
        # the store is shared by the tables of the connection, without recurse GeoServer refuses to drop a used one
        if not _store.get_resources():
            _catalog.delete(_store)
