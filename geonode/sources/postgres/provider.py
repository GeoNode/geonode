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
import dataclasses
import logging
import typing
from urllib.parse import urlencode

import psycopg2
from psycopg2.extensions import make_dsn
from osgeo import gdal, ogr
from django.utils.translation import gettext_lazy as _

from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.resource.models import ExecutionRequest
from geonode.security.auth_registry import auth_handler_registry
from geonode.security.models import AuthConfig
from geonode.sources.postgres.auth import PostgresAuthHandler
from geonode.sources.postgres.serializers import PostgresConnectionSerializer
from geonode.sources.base import BaseSourceProvider, BrowseEntry, Capability
from geonode.sources.models import DataItem
from geonode.upload.celery_tasks import import_orchestrator
from geonode.upload.handlers.postgres.handler import PostgresUploadHandler
from geonode.upload.orchestrator import orchestrator

logger = logging.getLogger(__name__)


class PostgresSourceProvider(BaseSourceProvider):
    """
    Tables and views of a PostgreSQL database, listed through the OGR PostgreSQL driver.
    Works with or without the PostGIS extension: plain tables simply have no geometries.
    The uri is postgresql:?schema=<schema>&table=<table>, relative to the connection that stores host and credentials
    """

    key = "postgresql"
    label = _("PostgreSQL / PostGIS")
    # for now the items are only looked at, never changed
    declared_capabilities = Capability.READ
    connection_serializer = PostgresConnectionSerializer

    CONNECT_TIMEOUT = 5
    STATEMENT_TIMEOUT_MS = 30000

    def _dsn(self, handler: PostgresAuthHandler) -> str:
        # make_dsn quotes the values, a password with spaces or quotes stays a single parameter
        return make_dsn(
            **handler.get_connection_params(),
            connect_timeout=self.CONNECT_TIMEOUT,
            application_name="geonode-sources",
            options=f"-c default_transaction_read_only=on -c statement_timeout={self.STATEMENT_TIMEOUT_MS}",
        )

    def test_connection(self, auth_config: AuthConfig) -> typing.Tuple[bool, str]:
        # credentials are checked during the handshake, no query is needed
        try:
            psycopg2.connect(self._dsn(auth_handler_registry.build(auth_config))).close()
            return True, ""
        except psycopg2.Error as e:
            # the driver message may expose server details, the caller only gets a generic reason
            logger.exception(e)
            return False, str(_("Could not connect with the provided parameters"))

    def browse(self, auth_config: AuthConfig) -> typing.List[BrowseEntry]:
        """List the tables of the connection schema, one entry per table"""
        handler = auth_handler_registry.build(auth_config)
        with (
            gdal.ExceptionMgr(),
            gdal.OpenEx(
                f"PG:{self._dsn(handler)}",
                gdal.OF_VECTOR | gdal.OF_READONLY,
                # with a single schema OGR makes it the active one and drops it from the layer names
                open_options=["LIST_ALL_TABLES=YES", f"SCHEMAS={handler.schema}"],
            ) as dataset,
        ):
            return [self._to_browse_entry(handler, dataset.GetLayer(idx)) for idx in range(dataset.GetLayerCount())]

    def _to_browse_entry(self, handler: PostgresAuthHandler, layer) -> BrowseEntry:
        schema, table = handler.schema, layer.GetName()
        defn = layer.GetLayerDefn()
        geometries = []
        for idx in range(defn.GetGeomFieldCount()):
            field = defn.GetGeomFieldDefn(idx)
            srs = field.GetSpatialRef()
            geometries.append(
                {
                    "column": field.GetName(),
                    "type": ogr.GeometryTypeToName(field.GetType()),
                    "srid": srs.GetAuthorityCode(None) if srs else None,
                }
            )
        return BrowseEntry(
            # the scheme is the provider key, so that the uri always tells which provider reads it
            uri=f"{self.key}:?{urlencode({'schema': schema, 'table': table})}",
            title=f"{schema}.{table}",
            details={"schema": schema, "table": table, "geometries": geometries},
        )

    def publish(self, auth_config: AuthConfig, entries: typing.List[BrowseEntry], user) -> typing.Dict[str, str]:
        """Publish each table in the local GeoServer through the importer, which stores it as a data item once done"""
        _handler = PostgresUploadHandler()
        _action = exa.UPLOAD.value
        _step = _handler.get_task_list(_action)[0]
        # a table still publishing keeps its execution: a duplicate one would roll back the first layer
        _executions = dict(
            ExecutionRequest.objects.filter(
                input_params__auth_config_id=auth_config.pk,
                input_params__uri__in=[_entry.uri for _entry in entries],
                status__in=[ExecutionRequest.STATUS_READY, ExecutionRequest.STATUS_RUNNING],
            ).values_list("input_params__uri", "exec_id")
        )
        for _entry in entries:
            if _entry.uri in _executions:
                continue
            # one table per execution: without GeoNode resources the orchestrator closes it at the first finished layer
            _exec_id = str(
                orchestrator.create_execution_request(
                    user=user,
                    func_name=_step,
                    step=_step,
                    input_params={
                        "handler_module_path": str(_handler),
                        # nothing is uploaded: the importer steps still expect the key
                        "files": {},
                        "source_provider": self.key,
                        "auth_config_id": auth_config.pk,
                        **dataclasses.asdict(_entry),
                    },
                    action=_action,
                    name=_entry.title,
                )
            )
            import_orchestrator.s({}, _exec_id, handler=str(_handler), action=_action, step=_step).apply_async()
            _executions[_entry.uri] = _exec_id
        return {_uri: str(_exec_id) for _uri, _exec_id in _executions.items()}

    def unpublish(self, data_item: DataItem) -> None:
        if data_item.layer:
            PostgresUploadHandler().remove_layer(data_item.auth_config_id, data_item.layer)
