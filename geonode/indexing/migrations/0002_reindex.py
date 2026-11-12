# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2025 OSGeo
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

from django.db import migrations
from django.core.management import call_command

logger = logging.getLogger(__name__)


def run_reindex(apps, schema_editor):
    try:
        logger.info("Running reindex migration to populate search indexes...")
        call_command("reindex")
        logger.info("Reindex migration completed successfully.")
    except Exception as e:
        logger.error(f"Reindex migration failed: {e}", exc_info=True)


class Migration(migrations.Migration):

    dependencies = [
        ("indexing", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(run_reindex, migrations.RunPython.noop),
    ]
