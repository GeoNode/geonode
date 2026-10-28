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
from urllib.parse import urlencode

import psycopg2
from psycopg2.extensions import make_dsn
from osgeo import gdal, ogr
from django.utils.translation import gettext_lazy as _

from geonode.security.auth_registry import auth_handler_registry
from geonode.security.models import AuthConfig
from geonode.sources.postgres.auth import PostgresAuthHandler
from geonode.sources.postgres.forms import PostgresConnectionForm
from geonode.sources.base import BaseSourceProvider, BrowseEntry, Capability

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
    connection_form = PostgresConnectionForm

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
