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
from . import init_registered_members_groupprofile
from django.apps import AppConfig
from geonode.groups.conf import settings

try:
    from django.db.models.signals import post_migrate
except Exception:
    # OR for Django 2.0+
    from django.db.backends.signals import post_migrate

logger = logging.getLogger(__name__)


def post_migration_callback(sender, **kwargs):
    if settings.AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME:
        logger.debug("Invoking 'init_registered_members_groupprofile'")
        init_registered_members_groupprofile()


class GroupsAppConfig(AppConfig):
    name = 'geonode.groups'

    def ready(self):
        post_migrate.connect(post_migration_callback, sender=self)
