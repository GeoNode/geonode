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
import tempfile

from django.core.management import call_command

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
            kwargs = {'backup_dir': tmp_dir}

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
            kwargs = {'backup_dir': tmp_dir}

            call_command('backup', *args, **kwargs)

            # make sure Configuration wasn't called at all
            self.assertEqual(mock_configuration_save.call_count, 0)
