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

from unittest.mock import patch, MagicMock
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from geonode.geoserver.management.commands.gwc_subcommands.truncate import (
    truncate_all_layers,
    truncate_layers,
)


class GwcManagementCommandTest(TestCase):
    @patch("geonode.geoserver.helpers.http_client.post")
    def test_truncate_layer_calls_api(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = (mock_response, "")

        truncate_layers(["test_layer1", "test_layer2"])

        self.assertEqual(mock_post.call_count, 2)

        call_args_1 = mock_post.call_args_list[0][1]
        self.assertIn(
            "<truncateLayer><layerName>test_layer1</layerName></truncateLayer>",
            call_args_1["data"].replace(" ", "").replace("\n", ""),
        )

        call_args_2 = mock_post.call_args_list[1][1]
        self.assertIn(
            "<truncateLayer><layerName>test_layer2</layerName></truncateLayer>",
            call_args_2["data"].replace(" ", "").replace("\n", ""),
        )

    @patch("geonode.geoserver.management.commands.gwc_subcommands.truncate.http_client.post")
    def test_truncate_all_calls_api(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = (mock_response, "")

        truncate_all_layers()

        self.assertEqual(mock_post.call_count, 1)
        self.assertIn("<truncateAll></truncateAll>", mock_post.call_args[1]["data"])

    @patch("geonode.geoserver.management.commands.gwc.truncate_layers")
    def test_management_command_layers(self, mock_truncate_layers):
        call_command("gwc", "truncate", "-l", "layer1", "-l", "layer2")
        mock_truncate_layers.assert_called_once_with(["layer1", "layer2"])

    @patch("geonode.geoserver.management.commands.gwc.truncate_all_layers")
    def test_management_command_all(self, mock_truncate_all):
        call_command("gwc", "truncate", "--all")
        mock_truncate_all.assert_called_once()

    def test_management_command_error_missing_args(self):
        with self.assertRaises(CommandError) as context:
            call_command("gwc", "truncate")
        self.assertIn("requires either the -l/--layer parameter(s) or the --all flag", str(context.exception))

    def test_management_command_error_both_args(self):
        with self.assertRaises(CommandError) as context:
            call_command("gwc", "truncate", "-l", "layer1", "--all")
        self.assertIn("Cannot use both -l/--layer and --all at the same time", str(context.exception))
