#########################################################################
#
# Copyright (C) 2016 OSGeo
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

from django.apps import AppConfig
from django.utils.translation import gettext_noop as _

from geonode.notifications_helper import NotificationsAppConfigBase

logger = logging.getLogger(__name__)


def create_geonode_db_schema(sender, using, **kwargs):
    """Create the configured PostgreSQL schema before migrations run."""
    import re
    from django.conf import settings
    from django.db import connections
    from geonode.utils import get_db_schema

    db_config = settings.DATABASES.get(using, {})
    schema = get_db_schema(db_config)

    if not schema or schema == "public":
        return

    if not re.match(r"^[A-Za-z_][A-Za-z0-9_$]*$", schema):
        logger.warning(f"Skipping schema creation for '{schema}' on database '{using}': invalid schema name")
        return

    try:
        with connections[using].cursor() as cursor:
            cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
    except Exception as e:
        logger.warning(f"Could not create schema '{schema}' on database '{using}': {e}")


class BaseAppConfig(NotificationsAppConfigBase, AppConfig):
    name = "geonode.base"
    default_auto_field = "django.db.models.BigAutoField"
    NOTIFICATIONS = (
        (
            "request_download_resourcebase",
            _("Request to download a resource"),
            _("A request for downloading a resource was sent"),
        ),
        (
            "request_resource_edit",
            _("Request resource change"),
            _("Owner has requested permissions to modify a resource"),
        ),
        (
            "resourcebase_created",
            _("Resource is created"),
            _("Resource is created"),
        ),
    )

    def ready(self):
        """Finalize setup"""
        from django.db.models import signals
        from geonode.base.signals import connect_signals

        connect_signals()
        signals.pre_migrate.connect(create_geonode_db_schema)

        super(BaseAppConfig, self).ready()
