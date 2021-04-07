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
import zipfile
import tempfile

from django.core.management import call_command
from django.core.management.base import CommandError

from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.br.tests.factories import RestoredBackupFactory
from geonode.br.management.commands.utils.utils import md5_file_hash
from geonode.base.models import Configuration


class RestoreCommandTests(GeoNodeBaseTestSupport):

    def setUp(self):
        super().setUp()
        # make sure Configuration exists in the database for Read Only mode tests
        Configuration.load()

    # force restore interruption before starting the procedure itself
    @mock.patch('geonode.br.management.commands.utils.utils.confirm', return_value=False)
    def test_with_logs_success(self, fake_confirm):

        # create the backup file
        with tempfile.NamedTemporaryFile() as tmp_file:
            with zipfile.ZipFile(tmp_file, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('something.txt', 'Some Content Here')

            # create an entry in restoration history with the same dump's hash
            RestoredBackupFactory(archive_md5='91162629d258a876ee994e9233b2ad87')

            args = ['-l']
            kwargs = {
                'backup_file': tmp_file.name,
                'config': os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    '..',
                    'management/commands/settings_sample.ini'
                )
            }

            call_command('restore', *args, **kwargs)

    # force restore interruption before starting the procedure itself
    @mock.patch('geonode.br.management.commands.utils.utils.confirm', return_value=False)
    def test_with_logs_failure(self, fake_confirm):

        # create the backup file
        with tempfile.NamedTemporaryFile() as tmp_file:
            with zipfile.ZipFile(tmp_file, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('something.txt', 'Some Content Here')

            # create an entry in restoration history with the same dump's hash
            RestoredBackupFactory(archive_md5=md5_file_hash(tmp_file.name))

            args = ['-l']
            kwargs = {
                'backup_file': tmp_file.name,
                'config': os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    '..',
                    'management/commands/settings_sample.ini'
                )
            }

            with self.assertRaises(RuntimeError) as exc:
                call_command('restore', *args, **kwargs)

            self.assertIn(
                'Backup archive has already been restored',
                exc.exception.args[0],
                '"Backup archive has already been restored" exception expected.'
            )

    # force backup interruption before starting the procedure itself
    @mock.patch('geonode.br.management.commands.utils.utils.confirm', return_value=False)
    # mock geonode.base.models.Configuration save() method
    @mock.patch('geonode.base.models.Configuration.save', return_value=None)
    def test_with_read_only_mode(self, mock_configuration_save, fake_confirm):

        # create the backup file
        with tempfile.NamedTemporaryFile() as tmp_file:
            with zipfile.ZipFile(tmp_file, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('something.txt', 'Some Content Here')

            args = []
            kwargs = {
                'backup_file': tmp_file.name,
                'config': os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    '..',
                    'management/commands/settings_sample.ini'
                )
            }

            call_command('restore', *args, **kwargs)

            # make sure Configuration was saved twice (Read-Only set, and revert)
            self.assertEqual(mock_configuration_save.call_count, 2)

    # force backup interruption before starting the procedure itself
    @mock.patch('geonode.br.management.commands.utils.utils.confirm', return_value=False)
    # mock geonode.base.models.Configuration save() method
    @mock.patch('geonode.base.models.Configuration.save', return_value=None)
    def test_without_read_only_mode(self, mock_configuration_save, fake_confirm):

        # create the backup file
        with tempfile.NamedTemporaryFile() as tmp_file:
            with zipfile.ZipFile(tmp_file, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('something.txt', 'Some Content Here')

            args = ['--skip-read-only']
            kwargs = {
                'backup_file': tmp_file.name,
                'config': os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    '..',
                    'management/commands/settings_sample.ini'
                )
            }

            call_command('restore', *args, **kwargs)

            # make sure Configuration wasn't called at all
            self.assertEqual(mock_configuration_save.call_count, 0)

    # force backup interruption before starting the procedure itself
    @mock.patch('geonode.br.management.commands.utils.utils.confirm', return_value=False)
    # mock geonode.base.models.Configuration save() method
    @mock.patch('geonode.base.models.Configuration.save', return_value=None)
    def test_config_files(self, mock_configuration_save, fake_confirm):

        # create the backup file
        with tempfile.NamedTemporaryFile() as tmp_file:
            with zipfile.ZipFile(tmp_file, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('something.txt', 'Some Content Here')

            args = ['--skip-read-only']
            kwargs = {
                'backup_file': tmp_file.name
            }

            with self.assertRaises(CommandError) as exc:
                call_command('restore', *args, **kwargs)

            self.assertIn(
                'Mandatory option (-c / --config)',
                exc.exception.args[0],
                '"Mandatory option (-c / --config)" exception expected.'
            )

        # create the backup file with ini file
        with tempfile.NamedTemporaryFile() as tmp_file:
            with zipfile.ZipFile(tmp_file, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('something.txt', 'Some Content Here')

            tmp_ini_file = f"{tmp_file.name.rsplit('.', 1)[0]}.ini"
            from configparser import ConfigParser
            config = ConfigParser()
            config['database'] = {
                'pgdump': 'pg_dump',
                'pgrestore': 'pg_restore'
            }

            config['geoserver'] = {
                'datadir': 'geoserver/data',
                'dumpvectordata': 'yes',
                'dumprasterdata': 'yes'
            }

            config['fixtures'] = {
                'apps': 'fake',
                'dumps': 'fake'
            }

            with open(tmp_ini_file, 'w') as configfile:
                config.write(configfile)

            args = ['--skip-read-only']
            kwargs = {
                'backup_file': tmp_file.name
            }

            call_command('restore', *args, **kwargs)
