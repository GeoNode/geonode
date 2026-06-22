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

from django.core.management.base import BaseCommand, CommandError

from geonode.base.management.command_utils import setup_logger
from geonode.geoserver.management.commands.gwc_subcommands import truncate
from geonode.geoserver.management.commands.gwc_subcommands.create import CreateTileLayers

logger = setup_logger()

COMMAND_TRUNCATE = "truncate"
COMMAND_CREATE = "create"
COMMANDS = [COMMAND_CREATE, COMMAND_TRUNCATE]


class Command(BaseCommand):
    help = f"Handles GWC commands {COMMANDS}"

    def _add_common_arguments(self, parser):
        parser.add_argument(
            '-d',
            '--dry-run',
            dest="dry-run",
            action='store_true',
            help="Do not actually perform any change on GWC")

        parser.add_argument(
            '--debug',
            dest="debug",
            action='store_true',
            help="Show debug logging")

    def add_arguments(self, parser):

        subparsers = parser.add_subparsers(dest="subcommand", required=True)

        parser_truncate = subparsers.add_parser(COMMAND_TRUNCATE, help="Truncate tile layers")
        truncate.add_arguments(parser_truncate)
        self._add_common_arguments(parser_truncate)

        parser_create = subparsers.add_parser(COMMAND_CREATE, help="Create tile layers")
        CreateTileLayers().add_arguments(parser_create)
        self._add_common_arguments(parser_create)

    def handle(self, *args, **options):
        subcommand = options["subcommand"]
        logger.info(f"Executing GWC subcommand '{subcommand}'...")

        if subcommand == COMMAND_TRUNCATE:
            truncate.handle(options)
        elif subcommand == COMMAND_CREATE:
            CreateTileLayers().handle(**options)
        else:
            raise CommandError(f"Unknown subcommand: {subcommand}")

        logger.info(f"GWC subcommand {subcommand} completed.")
