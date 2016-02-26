#########################################################################
#
# Copyright (C) 2016 OpenPlans
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
import os, sys
import shutil
import helpers
import tempfile

from optparse import make_option

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):

    help = 'Restore the GeoNode application data'

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
            help='Backup archive containing GeoNode data to restore.'))

    def handle(self, **options):
        ignore_errors = options.get('ignore_errors')
        backup_file = options.get('backup_file')

        if not backup_file or len(backup_file) == 0:
            raise CommandError("Backup archive '--backup-file' is mandatory")

        if helpers.confirm(prompt='WARNING: The restore will overwrite all your GeoNode data and files. Are you sure you want to proceed?', resp=False):
            # Create Target Folder
            restore_folder = os.path.join(tempfile.gettempdir(), 'restore')
            if not os.path.exists(restore_folder):
                os.makedirs(restore_folder)

            # Extract ZIP Archive to Target Folder
            target_folder = helpers.unzip_file(backup_file, restore_folder)

            # Prepare Target DB
            try:
                call_command('syncdb', interactive=False, load_initial_data=False)
                call_command('flush', interactive=False, load_initial_data=False)

                helpers.patch_db()
            except:
                traceback.print_exc()

            # Restore Fixtures
            for app_name, dump_name in zip(helpers.app_names, helpers.dump_names):
                fixture_file = os.path.join(target_folder, dump_name+'.json')

                print "Deserializing "+fixture_file
                try:
                    call_command('loaddata', fixture_file, app_label=app_name)
                except:
                    #traceback.print_exc()
                    print "WARNING: No valid fixture data found for '"+dump_name+"'."
                    #helpers.load_fixture(app_name, fixture_file)

            # Restore Media Root
            media_root = settings.MEDIA_ROOT
            media_folder = os.path.join(target_folder, helpers.MEDIA_ROOT)

            try:
                shutil.rmtree(media_root)
            except:
                pass

            if not os.path.exists(media_root):
                os.makedirs(media_root)

            helpers.copy_tree(media_folder, media_root)
            helpers.chmod_tree(media_root)
            print "Media Files Restored into '"+media_root+"'."

            # Restore Static Root
            static_root = settings.STATIC_ROOT
            static_folder = os.path.join(target_folder, helpers.STATIC_ROOT)

            try:
                shutil.rmtree(static_root)
            except:
                pass

            if not os.path.exists(static_root):
                os.makedirs(static_root)

            helpers.copy_tree(static_folder, static_root)
            helpers.chmod_tree(static_root)
            print "Static Root Restored into '"+static_root+"'."
          
            # Restore Static Root
            static_root = settings.STATIC_ROOT
            static_folder = os.path.join(target_folder, helpers.STATIC_ROOT)

            try:
                shutil.rmtree(static_root)
            except:
                pass

            if not os.path.exists(static_root):
                os.makedirs(static_root)

            helpers.copy_tree(static_folder, static_root)
            helpers.chmod_tree(static_root)
            print "Static Root Restored into '"+static_root+"'."

            # Restore Static Folders
            static_folders = settings.STATICFILES_DIRS
            static_files_folders = os.path.join(target_folder, helpers.STATICFILES_DIRS)

            for static_files_folder in static_folders:

                try:
                    shutil.rmtree(static_files_folder)
                except:
                    pass

                if not os.path.exists(static_files_folder):
                    os.makedirs(static_files_folder)

                helpers.copy_tree(os.path.join(static_files_folders, os.path.basename(os.path.normpath(static_files_folder))), static_files_folder)
                helpers.chmod_tree(static_files_folder)
                print "Static Files Restored into '"+static_files_folder+"'."

            # Restore Template Folders
            template_folders = settings.TEMPLATE_DIRS
            template_files_folders = os.path.join(target_folder, helpers.TEMPLATE_DIRS)

            for template_files_folder in template_folders:

                try:
                    shutil.rmtree(template_files_folder)
                except:
                    pass

                if not os.path.exists(template_files_folder):
                    os.makedirs(template_files_folder)

                helpers.copy_tree(os.path.join(template_files_folders, os.path.basename(os.path.normpath(template_files_folder))), template_files_folder)
                helpers.chmod_tree(template_files_folder)
                print "Template Files Restored into '"+template_files_folder+"'."

            # Restore Locale Folders
            locale_folders = settings.LOCALE_PATHS
            locale_files_folders = os.path.join(target_folder, helpers.LOCALE_PATHS)

            for locale_files_folder in locale_folders:

                try:
                    shutil.rmtree(locale_files_folder)
                except:
                    pass

                if not os.path.exists(locale_files_folder):
                    os.makedirs(locale_files_folder)

                helpers.copy_tree(os.path.join(locale_files_folders, os.path.basename(os.path.normpath(locale_files_folder))), locale_files_folder)
                helpers.chmod_tree(locale_files_folder)
                print "Locale Files Restored into '"+locale_files_folder+"'."

            # Cleanup DB
            try:
                helpers.cleanup_db()
            except:
                traceback.print_exc()

            print "Restore finished. Please find restored files and dumps into: '"+target_folder+"'."
        
