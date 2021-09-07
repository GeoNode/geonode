#########################################################################
#
# Copyright (C) 2021 OSGeo
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
import io
import logging

from django.core.management import (
    get_commands,
    load_command_class
)

logger = logging.getLogger(__name__)


def get_management_commands():
    """
    Get the list of all management commands, filter by the attr injected by the
    decorator and returns a dict with the app and command class.
    """
    available_commands = {}
    mngmt_commands = get_commands()

    for name, app_name in mngmt_commands.items():
        # Load command
        try:
            command_class = load_command_class(app_name, name)
        except (ImportError, AttributeError) as exception:
            logging.info(
                f'Command "{name}" from app "{app_name}" cannot be listed or ' f'used by http, exception: "{exception}"'
            )
            continue

        # Verify if its exposed
        is_exposed = hasattr(command_class, "expose_command_over_http") and command_class.expose_command_over_http
        if is_exposed:
            available_commands[name] = {
                "app": app_name,
                "command_class": command_class,
            }

    return available_commands


def get_management_command_details(command_class, command_name):
    """
    Get the help output of the management command.
    """
    parser = command_class.create_parser('', command_name)
    with io.StringIO() as output:
        parser.print_help(output)
        cmd_help_output = output.getvalue()
    return cmd_help_output
