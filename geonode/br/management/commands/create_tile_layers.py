# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2023 OSGeo
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
from django.core.management.base import BaseCommand
from typing_extensions import deprecated

from geonode.geoserver.management.commands.gwc_subcommands.create import CreateTileLayers as gwc_create

logger = logging.getLogger(__name__)


@deprecated("THIS COMMAND IS DEPRECATED - USE THE gwc COMMAND INSTEAD")
class Command(BaseCommand):
    help = "DEPRECATED COMMAND - USE gwc COMMAND INSTEAD - Create missing TileLayers in GWC"

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--force",
            dest="force",
            action="store_true",
            help="Force tile layer re-creation also if it already exists in GWC",
        )

        parser.add_argument("-l", "--layer", dest="layers", action="append", help="Only process specified layers ")

        parser.add_argument(
            "-d", "--dry-run", dest="dry-run", action="store_true", help="Do not actually perform any change on GWC"
        )

    def handle(self, **options):
        logger.error("THIS COMMAND IS DEPRECATED - USE THE gwc COMMAND INSTEAD")

        force = options.get("force")
        requested_layers = options.get("layers") or []
        dry_run = options.get("dry-run")

        logger.debug(f"FORCE is {force}")
        logger.debug(f"DRY-RUN is {dry_run}")
        logger.debug(f"LAYERS is {requested_layers}")

        subcommand = gwc_create()
        subcommand.run(
            force=force, requested_layers=requested_layers, create_all=len(requested_layers) == 0, dry_run=dry_run
        )
