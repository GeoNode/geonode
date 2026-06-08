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
from geonode.geoserver.management.commands.gwc_subcommands.truncate import (
    truncate_layers,
    truncate_all_layers,
)

logger = setup_logger()

COMMAND_TRUNCATE = "truncate"
COMMANDS = [COMMAND_TRUNCATE]


class Command(BaseCommand):
    help = f"Handles GWC commands {COMMANDS}"

    def add_arguments(self, parser):
        parser.add_argument("subcommand", nargs="?", choices=COMMANDS, help="GWC operation to run")

        truncate_group = parser.add_argument_group('Params for "truncate" subcommand')
        truncate_group.add_argument(
            "-l",
            "--layer",
            dest="layers",
            action="append",
            help="Name of the layer(s) to truncate. Can be repeated.",
        )
        truncate_group.add_argument(
            "--all",
            dest="truncate_all",
            action="store_true",
            help="Truncate all cache in GWC",
        )

    def handle(self, *args, **options):
        subcommand = options["subcommand"]
        logger.info("Starting GWC command.")

        if not subcommand:
            logger.warning("No GWC subcommand provided.")
            self.print_help("manage.py", "gwc")
            return

        logger.info("Executing GWC subcommand '%s'.", subcommand)

        if subcommand == COMMAND_TRUNCATE:
            layers = options.get("layers") or []
            truncate_all = options.get("truncate_all") or False

            logger.info(
                "Truncate command received. layers=%s, truncate_all=%s",
                layers,
                truncate_all,
            )

            if not layers and not truncate_all:
                raise CommandError("'truncate' command requires either the -l/--layer parameter(s) or the --all flag.")

            if layers and truncate_all:
                raise CommandError("Cannot use both -l/--layer and --all at the same time.")

            if truncate_all:
                truncate_all_layers()
            else:
                logger.info(f"Truncating {len(layers)} layer{'s' if len(layers) > 1 else ''}")
                truncate_layers(layers)

        else:
            raise CommandError(f"Unknown subcommand: {subcommand}")
