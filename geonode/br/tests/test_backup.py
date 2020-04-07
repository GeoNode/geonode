# -*- coding: utf-8 -*-
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

import os
import mock
import tempfile

from django.core.management import call_command
from django.core.management.base import CommandError

from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.base.models import Configuration


class BackupCommandTests(GeoNodeBaseTestSupport):

    def setUp(self):
        super().setUp()
        # make sure Configuration exists in the database for Read Only mode tests
        Configuration.load()

    # force backup interruption before starting the procedure itself
    @mock.patch('geonode.br.management.commands.utils.utils.confirm', return_value=False)
    # mock geonode.base.models.Configuration save() method
    @mock.patch('geonode.base.models.Configuration.save', return_value=None)
    def test_with_read_only_mode(self, mock_configuration_save, fake_confirm):
        with tempfile.TemporaryDirectory() as tmp_dir:
            args = []
            kwargs = {
                'backup_dir': tmp_dir,
                'config': os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    '..',
                    'management/commands/settings_sample.ini'
                )
            }

            call_command('backup', *args, **kwargs)

            # make sure Configuration was saved twice (Read-Only set, and revert)
            self.assertEqual(mock_configuration_save.call_count, 2)

    # force backup interruption before starting the procedure itself
    @mock.patch('geonode.br.management.commands.utils.utils.confirm', return_value=False)
    # mock geonode.base.models.Configuration save() method
    @mock.patch('geonode.base.models.Configuration.save', return_value=None)
    def test_without_read_only_mode(self, mock_configuration_save, fake_confirm):
        with tempfile.TemporaryDirectory() as tmp_dir:
            args = ['--skip-read-only']
            kwargs = {
                'backup_dir': tmp_dir,
                'config': os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    '..',
                    'management/commands/settings_sample.ini'
                )
            }

            call_command('backup', *args, **kwargs)

            # make sure Configuration wasn't called at all
            self.assertEqual(mock_configuration_save.call_count, 0)

    # force backup interruption before starting the procedure itself
    @mock.patch('geonode.br.management.commands.utils.utils.confirm', return_value=False)
    # mock geonode.base.models.Configuration save() method
    @mock.patch('geonode.base.models.Configuration.save', return_value=None)
    def test_config_file_not_provided(self, mock_configuration_save, fake_confirm):
        with tempfile.TemporaryDirectory() as tmp_dir:
            args = ['--skip-read-only']
            kwargs = {'backup_dir': tmp_dir}

            with self.assertRaises(CommandError) as exc:
                call_command('backup', *args, **kwargs)

            self.assertIn(
                'Mandatory option (-c / --config)',
                exc.exception.args[0],
                '"Mandatory option (-c / --config)" exception expected.'
            )

    # force backup interruption before starting the procedure itself
    @mock.patch('geonode.br.management.commands.utils.utils.confirm', return_value=False)
    # mock geonode.base.models.Configuration save() method
    @mock.patch('geonode.base.models.Configuration.save', return_value=None)
    def test_config_file_does_not_exist(self, mock_configuration_save, fake_confirm):
        with tempfile.TemporaryDirectory() as tmp_dir:
            args = ['--skip-read-only']
            kwargs = {'backup_dir': tmp_dir, 'config': '/some/random/path'}

            with self.assertRaises(CommandError) as exc:
                call_command('backup', *args, **kwargs)

            self.assertIn(
                "file does not exist",
                exc.exception.args[0],
                '"file does not exist" exception expected.'
            )
