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

from django.conf import settings
from django.core.management import get_commands, load_command_class

logger = logging.getLogger(__name__)


def get_management_commands():
    """
    Get the list of all exposed management commands.
    """
    return settings.MANAGEMENT_COMMANDS_EXPOSED_OVER_HTTP


def get_management_commands_apps():
    """
    Get a dict of all management commands, filter by the
    MANAGEMENT_COMMANDS_EXPOSED_OVER_HTTP setting.
    """
    mngmt_commands = get_commands()
    command_names = get_management_commands()
    available_commands = {name: mngmt_commands[name] for name in command_names}
    return available_commands


def get_management_command_details(command_name):
    """
    Get the help output of the management command.
    """
    app_name = get_management_commands_apps()[command_name]
    command_class = load_command_class(app_name, command_name)
    parser = command_class.create_parser("", command_name)
    with io.StringIO() as output:
        parser.print_help(output)
        cmd_help_output = output.getvalue()
    return cmd_help_output
