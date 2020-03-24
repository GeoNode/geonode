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

import mock
import zipfile
import tempfile

from django.core.management import call_command

from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.br.tests.factories import RestoredBackupFactory
from geonode.br.management.commands.utils.utils import md5_file_hash


class RestoreCommandTests(GeoNodeBaseTestSupport):

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
            kwargs = {'backup_file': tmp_file.name}

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
            kwargs = {'backup_file': tmp_file.name}

            with self.assertRaises(RuntimeError) as exc:
                call_command('restore', *args, **kwargs)

            self.assertIn(
                'Backup archive has already been restored',
                exc.exception.args[0],
                '"Backup archive has already been restored" exception expected.'
            )
