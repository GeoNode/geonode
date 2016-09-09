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

import traceback
import os
import helpers
import tempfile
import json

from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import (
    DEFAULT_DB_ALIAS
)


class Command(BaseCommand):

    help = 'Migrate existing Layers and Maps on GeoNode'

    option_list = BaseCommand.option_list + (
        make_option(
            '-i',
            '--ignore-errors',
            action='store_true',
            dest='ignore_errors',
            default=False,
            help='Stop after any errors are encountered.'),
        make_option(
            '--backup-file',
            dest='backup_file',
            type="string",
            help='Backup archive containing GeoNode data to restore.'),
        make_option(
            '--owner',
            dest='owner',
            type="string",
            help='New owner of the GeoNode Layers/Maps.'))

    def handle(self, **options):
        # ignore_errors = options.get('ignore_errors')
        backup_file = options.get('backup_file')
        owner = options.get('owner')

        if not backup_file or len(backup_file) == 0:
            raise CommandError("Backup archive '--backup-file' is mandatory")

        if not owner or len(owner) == 0:
            raise CommandError("Owner '--owner' is mandatory")

        message = 'WARNING: The migration may break GeoNode existing Layers. You want to proceed?'
        if helpers.confirm(prompt=message, resp=False):

            """Migrate existing Layers on GeoNode DB"""
            try:
                # Create Target Folder
                restore_folder = os.path.join(tempfile.gettempdir(), 'restore')
                if not os.path.exists(restore_folder):
                    os.makedirs(restore_folder)

                # Extract ZIP Archive to Target Folder
                target_folder = helpers.unzip_file(backup_file, restore_folder)

                # Retrieve the max Primary Key from the DB
                from geonode.base.models import ResourceBase
                try:
                    higher_pk = ResourceBase.objects.all().order_by("-id")[0].pk
                except:
                    higher_pk = 0

                # Restore Fixtures
                for app_name, dump_name in zip(helpers.app_names, helpers.dump_names):
                    for mig_name, mangler in zip(helpers.migrations, helpers.manglers):
                        if app_name == mig_name:
                            fixture_file = os.path.join(target_folder, dump_name+'.json')

                            print "Deserializing "+fixture_file
                            mangler = helpers.load_class(mangler)

                            obj = helpers.load_fixture(app_name, fixture_file, mangler=mangler,
                                                       basepk=higher_pk, owner=owner,
                                                       datastore=settings.OGC_SERVER['default']['DATASTORE'],
                                                       siteurl=settings.SITEURL)

                            from django.core import serializers

                            objects = serializers.deserialize('json', json.dumps(obj), ignorenonexistent=True)
                            for obj in objects:
                                obj.save(using=DEFAULT_DB_ALIAS)

                print "Restore finished. Please find restored files and dumps into: '"+target_folder+"'."

            except Exception:
                traceback.print_exc()
