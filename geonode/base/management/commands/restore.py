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

try:
    import json
except ImportError:
    from django.utils import simplejson as json
import traceback
import os
import time
import shutil
import requests
import tempfile
import helpers
from helpers import Config

from distutils import dir_util
from requests.auth import HTTPBasicAuth
from optparse import make_option

from geonode.utils import designals, resignals

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):

    help = 'Restore the GeoNode application data'

    option_list = BaseCommand.option_list + Config.geoserver_option_list + (
        Config.option,
        make_option(
            '-i',
            '--ignore-errors',
            action='store_true',
            dest='ignore_errors',
            default=False,
            help='Stop after any errors are encountered.'),
        make_option(
            '-f',
            '--force',
            action='store_true',
            dest='force_exec',
            default=False,
            help='Forces the execution without asking for confirmation.'),
        make_option(
            '--skip-geoserver',
            action='store_true',
            default=False,
            help='Skips geoserver backup'),
        make_option(
            '--backup-file',
            dest='backup_file',
            type="string",
            default=None,
            help='Backup archive containing GeoNode data to restore.'),
        make_option(
            '--backup-dir',
            dest='backup_dir',
            type="string",
            default=None,
            help='Backup directory containing GeoNode data to restore.'))

    def restore_geoserver_backup(self, settings, target_folder):
        """Restore GeoServer Catalog"""
        url = settings.OGC_SERVER['default']['PUBLIC_LOCATION']
        user = settings.OGC_SERVER['default']['USER']
        passwd = settings.OGC_SERVER['default']['PASSWORD']
        geoserver_bk_file = os.path.join(target_folder, 'geoserver_catalog.zip')

        if not os.path.exists(geoserver_bk_file):
            print('Skipping geoserver restore: ' +
                  'file "{}" not found.'.format(geoserver_bk_file))
            return

        print "Restoring 'GeoServer Catalog ["+url+"]' into '"+geoserver_bk_file+"'."

        # Best Effort Restore: 'options': {'option': ['BK_BEST_EFFORT=true']}
        data = {'restore': {'archiveFile': geoserver_bk_file, 'options': {}}}
        headers = {'Content-type': 'application/json'}
        r = requests.post(url + 'rest/br/restore/', data=json.dumps(data),
                          headers=headers, auth=HTTPBasicAuth(user, passwd))
        error_backup = 'Could not successfully restore GeoServer ' + \
                       'catalog [{}rest/br/backup/]: {} - {}'

        if (r.status_code > 201):

            try:
                gs_backup = r.json()
            except ValueError:
                raise ValueError(error_backup.format(url, r.status_code, r.text))

            gs_bk_exec_id = gs_backup['restore']['execution']['id']
            r = requests.get(url + 'rest/br/restore/' + str(gs_bk_exec_id) + '.json',
                             auth=HTTPBasicAuth(user, passwd))
            if (r.status_code == 200):

                try:
                    gs_backup = r.json()
                except ValueError:
                    raise ValueError(error_backup.format(url, r.status_code, r.text))

                gs_bk_progress = gs_backup['restore']['execution']['progress']
                print gs_bk_progress

            raise ValueError(error_backup.format(url, r.status_code, r.text))

        else:

            try:
                gs_backup = r.json()
            except ValueError:
                raise ValueError(error_backup.format(url, r.status_code, r.text))

            gs_bk_exec_id = gs_backup['restore']['execution']['id']
            r = requests.get(url + 'rest/br/restore/' + str(gs_bk_exec_id) + '.json',
                             auth=HTTPBasicAuth(user, passwd))
            if (r.status_code == 200):
                gs_bk_exec_status = gs_backup['restore']['execution']['status']
                gs_bk_exec_progress = gs_backup['restore']['execution']['progress']
                gs_bk_exec_progress_updated = '0/0'
                while (gs_bk_exec_status != 'COMPLETED' and gs_bk_exec_status != 'FAILED'):
                    if (gs_bk_exec_progress != gs_bk_exec_progress_updated):
                        gs_bk_exec_progress_updated = gs_bk_exec_progress
                    r = requests.get(url + 'rest/br/restore/' + str(gs_bk_exec_id) + '.json',
                                     auth=HTTPBasicAuth(user, passwd))
                    if (r.status_code == 200):

                        try:
                            gs_backup = r.json()
                        except ValueError:
                            raise ValueError(error_backup.format(url, r.status_code, r.text))

                        gs_bk_exec_status = gs_backup['restore']['execution']['status']
                        gs_bk_exec_progress = gs_backup['restore']['execution']['progress']
                        print str(gs_bk_exec_status) + ' - ' + gs_bk_exec_progress
                        time.sleep(3)
                    else:
                        raise ValueError(error_backup.format(url, r.status_code, r.text))
            else:
                raise ValueError(error_backup.format(url, r.status_code, r.text))

    def restore_geoserver_raster_data(self, config, settings, target_folder):
        if (config.gs_data_dir):
            if (config.gs_dump_raster_data):

                gs_data_folder = os.path.join(target_folder, 'gs_data_dir', 'data', 'geonode')
                if not os.path.exists(gs_data_folder):
                    print('Skipping geoserver raster data restore: ' +
                          'directory "{}" not found.'.format(gs_data_folder))
                    return

                # Restore '$config.gs_data_dir/data/geonode'
                gs_data_root = os.path.join(config.gs_data_dir, 'data', 'geonode')
                if not os.path.isabs(gs_data_root):
                    gs_data_root = os.path.join(settings.PROJECT_ROOT, '..', gs_data_root)

                try:
                    shutil.rmtree(gs_data_root)
                    print 'Cleaned out old GeoServer Data Dir: ' + gs_data_root
                except:
                    pass

                if not os.path.exists(gs_data_root):
                    os.makedirs(gs_data_root)

                helpers.copy_tree(gs_data_folder, gs_data_root)
                helpers.chmod_tree(gs_data_root)
                print "GeoServer Uploaded Data Restored to '"+gs_data_root+"'."

                # Cleanup '$config.gs_data_dir/gwc-layers'
                gwc_layers_root = os.path.join(config.gs_data_dir, 'gwc-layers')
                if not os.path.isabs(gwc_layers_root):
                    gwc_layers_root = os.path.join(settings.PROJECT_ROOT, '..', gwc_layers_root)

                try:
                    shutil.rmtree(gwc_layers_root)
                    print 'Cleaned out old GeoServer GWC Layers Config: ' + gwc_layers_root
                except:
                    pass

                if not os.path.exists(gwc_layers_root):
                    os.makedirs(gwc_layers_root)

    def restore_geoserver_vector_data(self, config, settings, target_folder):
        """Restore Vectorial Data from DB"""
        if (config.gs_dump_vector_data):

            gs_data_folder = os.path.join(target_folder, 'gs_data_dir', 'data', 'geonode')
            if not os.path.exists(gs_data_folder):
                print('Skipping geoserver vector data restore: ' +
                      'directory "{}" not found.'.format(gs_data_folder))
                return

            datastore = settings.OGC_SERVER['default']['DATASTORE']
            if (datastore):
                ogc_db_name = settings.DATABASES[datastore]['NAME']
                ogc_db_user = settings.DATABASES[datastore]['USER']
                ogc_db_passwd = settings.DATABASES[datastore]['PASSWORD']
                ogc_db_host = settings.DATABASES[datastore]['HOST']
                ogc_db_port = settings.DATABASES[datastore]['PORT']

                helpers.restore_db(config, ogc_db_name, ogc_db_user, ogc_db_port,
                                   ogc_db_host, ogc_db_passwd, gs_data_folder)

    def restore_geoserver_externals(self, config, settings, target_folder):
        """Restore external references from XML files"""
        external_folder = os.path.join(target_folder, helpers.EXTERNAL_ROOT)
        dir_util.copy_tree(external_folder, '/')

    def handle(self, **options):
        # ignore_errors = options.get('ignore_errors')
        config = Config(options)
        force_exec = options.get('force_exec')
        backup_file = options.get('backup_file')
        skip_geoserver = options.get('skip_geoserver')
        backup_dir = options.get('backup_dir')

        if not any([backup_file, backup_dir]):
            raise CommandError("Mandatory option (--backup-file|--backup-dir)")

        if all([backup_file, backup_dir]):
            raise CommandError("Exclusive option (--backup-file|--backup-dir)")

        if backup_file and not os.path.isfile(backup_file):
            raise CommandError("Provided '--backup-file' is not a file")

        if backup_dir and not os.path.isdir(backup_dir):
            raise CommandError("Provided '--backup-dir' is not a directory")

        print "Before proceeding with the Restore, please ensure that:"
        print " 1. The backend (DB or whatever) is accessible and you have rights"
        print " 2. The GeoServer is up and running and reachable from this machine"
        message = 'WARNING: The restore will overwrite ALL GeoNode data. You want to proceed?'
        if force_exec or helpers.confirm(prompt=message, resp=False):
            target_folder = backup_dir

            if backup_file:
                # Create Target Folder
                restore_folder = os.path.join(tempfile.gettempdir(), 'restore')
                if not os.path.exists(restore_folder):
                    os.makedirs(restore_folder)

                # Extract ZIP Archive to Target Folder
                target_folder = helpers.unzip_file(backup_file, restore_folder)

            if not skip_geoserver:
                self.restore_geoserver_backup(settings, target_folder)
                self.restore_geoserver_raster_data(config, settings, target_folder)
                self.restore_geoserver_vector_data(config, settings, target_folder)
                print("Restoring geoserver external resources")
                self.restore_geoserver_externals(config, settings, target_folder)
            else:
                print("Skipping geoserver backup restore")

            # Prepare Target DB
            try:
                call_command('migrate', interactive=False, load_initial_data=False)
                call_command('flush', interactive=False, load_initial_data=False)

                db_name = settings.DATABASES['default']['NAME']
                db_user = settings.DATABASES['default']['USER']
                db_port = settings.DATABASES['default']['PORT']
                db_host = settings.DATABASES['default']['HOST']
                db_passwd = settings.DATABASES['default']['PASSWORD']

                helpers.patch_db(db_name, db_user, db_port, db_host, db_passwd)
            except:
                traceback.print_exc()

            try:
                # Deactivate GeoNode Signals
                print "Deactivating GeoNode Signals..."
                designals()
                print "...done!"

                # Restore Fixtures
                for app_name, dump_name in zip(config.app_names, config.dump_names):
                    fixture_file = os.path.join(target_folder, dump_name+'.json')

                    print "Deserializing "+fixture_file
                    try:
                        call_command('loaddata', fixture_file, app_label=app_name)
                    except:
                        traceback.print_exc()
                        print "WARNING: No valid fixture data found for '"+dump_name+"'."
                        # helpers.load_fixture(app_name, fixture_file)

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

                    helpers.copy_tree(os.path.join(static_files_folders,
                                                   os.path.basename(os.path.normpath(static_files_folder))),
                                      static_files_folder)
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

                    helpers.copy_tree(os.path.join(template_files_folders,
                                                   os.path.basename(os.path.normpath(template_files_folder))),
                                      template_files_folder)
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

                    helpers.copy_tree(os.path.join(locale_files_folders,
                                                   os.path.basename(os.path.normpath(locale_files_folder))),
                                      locale_files_folder)
                    helpers.chmod_tree(locale_files_folder)
                    print "Locale Files Restored into '"+locale_files_folder+"'."

                # Cleanup DB
                try:
                    db_name = settings.DATABASES['default']['NAME']
                    db_user = settings.DATABASES['default']['USER']
                    db_port = settings.DATABASES['default']['PORT']
                    db_host = settings.DATABASES['default']['HOST']
                    db_passwd = settings.DATABASES['default']['PASSWORD']

                    helpers.cleanup_db(db_name, db_user, db_port, db_host, db_passwd)
                except:
                    traceback.print_exc()

                print "Restore finished. Please find restored files and dumps into:"

                return str(target_folder)

            finally:
                # Reactivate GeoNode Signals
                print "Reactivating GeoNode Signals..."
                resignals()
                print "...done!"
