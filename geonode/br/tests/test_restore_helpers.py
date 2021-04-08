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
import time
import zipfile
import tempfile
import datetime

from django.core.management.base import CommandError

from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.br.tests.factories import RestoredBackupFactory
from geonode.br.management.commands.utils.utils import md5_file_hash
from geonode.br.management.commands.restore import Command as RestoreCommand


class RestoreCommandHelpersTests(GeoNodeBaseTestSupport):
    # validate_backup_file_hash

    # validate_backup_file_options() method test
    def test_mandatory_option_failure(self):

        options = {}

        with self.assertRaises(CommandError) as exc:
            RestoreCommand().validate_backup_file_options(**options)

        self.assertIn(
            'Mandatory option',
            exc.exception.args[0],
            '"Mandatory option" failure exception expected.'
        )

    # validate_backup_file_options() method test
    def test_exclusive_option_failure(self):

        options = {
            'backup_file': '/some/random/path/1.zip',
            'backup_files_dir': '/some/random/path'
        }

        with self.assertRaises(CommandError) as exc:
            RestoreCommand().validate_backup_file_options(**options)

        self.assertIn(
            'Exclusive option',
            exc.exception.args[0],
            '"Exclusive option" failure exception expected.'
        )

    # validate_backup_file_options() method test
    def test_mandatory_option_backup_file_success(self):

        with tempfile.NamedTemporaryFile() as tmp:
            with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('something.txt', 'Some Content Here')

            options = {'backup_file': tmp.name}
            RestoreCommand().validate_backup_file_options(**options)

    # validate_backup_file_options() method test
    def test_mandatory_option_backup_file_failure(self):

        with tempfile.NamedTemporaryFile() as tmp:

            options = {'backup_file': tmp.name}

            with self.assertRaises(CommandError) as exc:
                RestoreCommand().validate_backup_file_options(**options)

            self.assertIn(
                'not a .zip file',
                exc.exception.args[0],
                '"not a .zip file" failure exception expected.'
            )

    # validate_backup_file_options() method test
    def test_mandatory_option_backup_files_dir_success(self):

        with tempfile.TemporaryDirectory() as tmp:
            options = {'backup_files_dir': tmp}
            RestoreCommand().validate_backup_file_options(**options)

    # validate_backup_file_options() method test
    def test_mandatory_option_backup_files_dir_failure(self):

        with tempfile.NamedTemporaryFile() as tmp:

            options = {'backup_files_dir': tmp.name}

            with self.assertRaises(CommandError) as exc:
                RestoreCommand().validate_backup_file_options(**options)

            self.assertIn(
                'not a directory',
                exc.exception.args[0],
                '"not a directory" failure exception expected.'
            )

    # parse_backup_files_dir() method test
    def test_backup_files_dir_no_archive(self):

        with tempfile.TemporaryDirectory() as tmp:

            backup_file = RestoreCommand().parse_backup_files_dir(tmp)
            self.assertIsNone(backup_file, 'Expecting backup file to be None')

    # parse_backup_files_dir() method test
    def test_backup_files_dir_multiple_archives(self):

        # create a backup files directory
        with tempfile.TemporaryDirectory() as tmp_dir:

            # create the 1st backup file
            with tempfile.NamedTemporaryFile(dir=tmp_dir) as tmp_file_1:
                with zipfile.ZipFile(tmp_file_1, 'w', zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr('something1.txt', 'Some Content Here')

                # make sure timestamps of files modification differ
                time.sleep(1)

                # create the 2nd backup file
                with tempfile.NamedTemporaryFile(dir=tmp_dir) as tmp_file_2:
                    with zipfile.ZipFile(tmp_file_2, 'w', zipfile.ZIP_DEFLATED) as archive:
                        archive.writestr('something2.txt', 'Some Content Here')

                    backup_file = RestoreCommand().parse_backup_files_dir(tmp_dir)

                    self.assertIn(tmp_file_2.name, backup_file, 'Expected the younger file to be chosen.')

    # parse_backup_files_dir() method test
    def test_backup_files_dir_with_newer_restored_backup(self):

        # create an entry in restoration history with a dump created in the future
        RestoredBackupFactory(creation_date=(datetime.datetime.now()) + datetime.timedelta(days=2))

        # create a backup files directory
        with tempfile.TemporaryDirectory() as tmp_dir:

            # create the backup file
            with tempfile.NamedTemporaryFile(dir=tmp_dir) as tmp_file:
                with zipfile.ZipFile(tmp_file, 'w', zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr('something.txt', 'Some Content Here')

                backup_file = RestoreCommand().parse_backup_files_dir(tmp_dir)

                self.assertIsNone(backup_file, 'Expected the backup not to be chosen.')

    # parse_backup_files_dir() method test
    def test_backup_files_dir_with_older_restored_backup(self):

        # create an entry in restoration history with a dump created in the past
        RestoredBackupFactory(creation_date=(datetime.datetime.now()) - datetime.timedelta(days=2))

        # create a backup files directory
        with tempfile.TemporaryDirectory() as tmp_dir:

            # create the backup file
            with tempfile.NamedTemporaryFile(dir=tmp_dir) as tmp_file:
                with zipfile.ZipFile(tmp_file, 'w', zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr('something.txt', 'Some Content Here')

                backup_file = RestoreCommand().parse_backup_files_dir(tmp_dir)

                self.assertIn(tmp_file.name, backup_file, 'Expected the backup to be chosen.')

    # validate_backup_file_hash() method test
    def test_backup_hash_no_md5_file(self):

        # create the backup file
        with tempfile.NamedTemporaryFile() as tmp_file:
            with zipfile.ZipFile(tmp_file, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('something.txt', 'Some Content Here')

            file_hash = RestoreCommand().validate_backup_file_hash(tmp_file.name)

            self.assertIsNotNone(file_hash, 'Expected the backup file MD5 hash to be returned.')

    # validate_backup_file_hash() method test
    def test_backup_hash_failure(self):

        # create the backup file
        with tempfile.NamedTemporaryFile() as tmp_file:
            with zipfile.ZipFile(tmp_file, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('something.txt', 'Some Content Here')

            # create a md5 hash file for the backup temporary file
            tmp_hash_file = f"{tmp_file.name}.md5"
            with open(tmp_hash_file, 'w') as hash_file:
                hash_file.write('91162629d258a876ee994e9233b2ad87')

            try:
                with self.assertRaises(RuntimeError) as exc:
                    RestoreCommand().validate_backup_file_hash(tmp_file.name)

                self.assertIn(
                    'Backup archive integrity failure',
                    exc.exception.args[0],
                    '"Backup archive integrity failure" exception expected.'
                )

            finally:
                # remove temporary hash file
                os.remove(tmp_hash_file)

    # validate_backup_file_hash() method test
    def test_backup_hash_success(self):

        # create the backup file
        with tempfile.NamedTemporaryFile() as tmp_file:
            with zipfile.ZipFile(tmp_file, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('something.txt', 'Some Content Here')

            # create a md5 hash file for the backup temporary file
            tmp_hash_file = f"{tmp_file.name}.md5"
            with open(tmp_hash_file, 'w') as hash_file:
                hash_file.write(md5_file_hash(tmp_file.name))

            try:
                file_hash = RestoreCommand().validate_backup_file_hash(tmp_file.name)

                self.assertIsNotNone(file_hash, 'Expected the backup file MD5 hash to be returned.')

            finally:
                # remove temporary hash file
                os.remove(tmp_hash_file)
