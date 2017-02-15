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
import shutil
import requests
import helpers
import simplejson as json

from requests.auth import HTTPBasicAuth
from optparse import make_option

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from geonode.utils import designals, resignals


class Command(BaseCommand):

    help = 'Backup the GeoNode application data'

    option_list = BaseCommand.option_list + (
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
            '--backup-dir',
            dest='backup_dir',
            type="string",
            help='Destination folder where to store the backup archive. It must be writable.'))

    def handle(self, **options):
        # ignore_errors = options.get('ignore_errors')
        force_exec = options.get('force_exec')
        backup_dir = options.get('backup_dir')

        if not backup_dir or len(backup_dir) == 0:
            raise CommandError("Destination folder '--backup-dir' is mandatory")

        print "Before proceeding with the Backup, please ensure that:"
        print " 1. The backend (DB or whatever) is accessible and you have rights"
        print " 2. The GeoServer is up and running and reachable from this machine"
        message = 'You want to proceed?'

        if force_exec or helpers.confirm(prompt=message, resp=False):
            # Create Target Folder
            dir_time_suffix = helpers.get_dir_time_suffix()
            target_folder = os.path.join(backup_dir, dir_time_suffix)
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            os.chmod(target_folder, 0755)

            # Create GeoServer Backup
            url = settings.OGC_SERVER['default']['PUBLIC_LOCATION']
            user = settings.OGC_SERVER['default']['USER']
            passwd = settings.OGC_SERVER['default']['PASSWORD']
            geoserver_bk_file = os.path.join(target_folder, 'geoserver_catalog.zip')

            print "Dumping 'GeoServer Catalog ["+url+"]' into '"+geoserver_bk_file+"'."
            data = {'backup': {'archiveFile': geoserver_bk_file, 'overwrite': 'true',
                               'options': {'option': ['BK_BEST_EFFORT=true']}}}
            headers = {'Content-type': 'application/json'}
            r = requests.post(url + 'rest/br/backup/', data=json.dumps(data),
                              headers=headers, auth=HTTPBasicAuth(user, passwd))
            if (r.status_code > 201):
                gs_backup = r.json()
                gs_bk_exec_id = gs_backup['backup']['execution']['id']
                r = requests.get(url + 'rest/br/backup/' + str(gs_bk_exec_id) + '.json',
                                 auth=HTTPBasicAuth(user, passwd))
                if (r.status_code == 200):
                    gs_backup = r.json()
                    gs_bk_progress = gs_backup['backup']['execution']['progress']
                    print gs_bk_progress

                raise ValueError('Could not successfully backup GeoServer catalog [' + url +
                                 'rest/br/backup/]: ' + str(r.status_code) + ' - ' + str(r.text))
            else:
                gs_backup = r.json()
                gs_bk_exec_id = gs_backup['backup']['execution']['id']
                r = requests.get(url + 'rest/br/backup/' + str(gs_bk_exec_id) + '.json',
                                 auth=HTTPBasicAuth(user, passwd))
                if (r.status_code == 200):
                    gs_bk_exec_status = gs_backup['backup']['execution']['status']
                    gs_bk_exec_progress = gs_backup['backup']['execution']['progress']
                    gs_bk_exec_progress_updated = '0/0'
                    while (gs_bk_exec_status != 'COMPLETED' and gs_bk_exec_status != 'FAILED'):
                        if (gs_bk_exec_progress != gs_bk_exec_progress_updated):
                            gs_bk_exec_progress_updated = gs_bk_exec_progress
                        r = requests.get(url + 'rest/br/backup/' + str(gs_bk_exec_id) + '.json',
                                         auth=HTTPBasicAuth(user, passwd))
                        if (r.status_code == 200):
                            gs_backup = r.json()
                            gs_bk_exec_status = gs_backup['backup']['execution']['status']
                            gs_bk_exec_progress = gs_backup['backup']['execution']['progress']
                            print str(gs_bk_exec_status) + ' - ' + gs_bk_exec_progress
                            time.sleep(3)
                        else:
                            raise ValueError('Could not successfully backup GeoServer catalog [' + url +
                                             'rest/br/backup/]: ' + str(r.status_code) + ' - ' + str(r.text))
                else:
                    raise ValueError('Could not successfully backup GeoServer catalog [' + url +
                                     'rest/br/backup/]: ' + str(r.status_code) + ' - ' + str(r.text))

            # Dump GeoServer Data
            if (helpers.GS_DATA_DIR):
                if (helpers.GS_DUMP_RASTER_DATA):
                    # Dump '$GS_DATA_DIR/data/geonode'
                    gs_data_root = os.path.join(helpers.GS_DATA_DIR, 'data', 'geonode')
                    gs_data_folder = os.path.join(target_folder, 'gs_data_dir', 'data', 'geonode')
                    if not os.path.exists(gs_data_folder):
                        os.makedirs(gs_data_folder)

                    helpers.copy_tree(gs_data_root, gs_data_folder)
                    print "Dumped GeoServer Uploaded Data from '"+gs_data_root+"'."

            if (helpers.GS_DUMP_VECTOR_DATA):
                # Dump Vectorial Data from DB
                datastore = settings.OGC_SERVER['default']['DATASTORE']
                if (datastore):
                    ogc_db_name = settings.DATABASES[datastore]['NAME']
                    ogc_db_user = settings.DATABASES[datastore]['USER']
                    ogc_db_passwd = settings.DATABASES[datastore]['PASSWORD']
                    ogc_db_host = settings.DATABASES[datastore]['HOST']
                    ogc_db_port = settings.DATABASES[datastore]['PORT']

                    gs_data_folder = os.path.join(target_folder, 'gs_data_dir', 'data', 'geonode')
                    if not os.path.exists(gs_data_folder):
                        os.makedirs(gs_data_folder)

                    helpers.dump_db(ogc_db_name, ogc_db_user, ogc_db_port, ogc_db_host, ogc_db_passwd, gs_data_folder)

            try:
                # Deactivate GeoNode Signals
                print "Deactivating GeoNode Signals..."
                designals()
                print "...done!"

                # Dump Fixtures
                for app_name, dump_name in zip(helpers.app_names, helpers.dump_names):
                    print "Dumping '"+app_name+"' into '"+dump_name+".json'."
                    # Point stdout at a file for dumping data to.
                    output = open(os.path.join(target_folder, dump_name+'.json'), 'w')
                    call_command('dumpdata', app_name, format='json', indent=2, natural=True, stdout=output)
                    output.close()

                # Store Media Root
                media_root = settings.MEDIA_ROOT
                media_folder = os.path.join(target_folder, helpers.MEDIA_ROOT)
                if not os.path.exists(media_folder):
                    os.makedirs(media_folder)

                helpers.copy_tree(media_root, media_folder)
                print "Saved Media Files from '"+media_root+"'."

                # Store Static Root
                static_root = settings.STATIC_ROOT
                static_folder = os.path.join(target_folder, helpers.STATIC_ROOT)
                if not os.path.exists(static_folder):
                    os.makedirs(static_folder)

                helpers.copy_tree(static_root, static_folder)
                print "Saved Static Root from '"+static_root+"'."

                # Store Static Folders
                static_folders = settings.STATICFILES_DIRS
                static_files_folders = os.path.join(target_folder, helpers.STATICFILES_DIRS)
                if not os.path.exists(static_files_folders):
                    os.makedirs(static_files_folders)

                for static_files_folder in static_folders:
                    static_folder = os.path.join(static_files_folders,
                                                 os.path.basename(os.path.normpath(static_files_folder)))
                    if not os.path.exists(static_folder):
                        os.makedirs(static_folder)

                    helpers.copy_tree(static_files_folder, static_folder)
                    print "Saved Static Files from '"+static_files_folder+"'."

                # Store Template Folders
                template_folders = settings.TEMPLATE_DIRS
                template_files_folders = os.path.join(target_folder, helpers.TEMPLATE_DIRS)
                if not os.path.exists(template_files_folders):
                    os.makedirs(template_files_folders)

                for template_files_folder in template_folders:
                    template_folder = os.path.join(template_files_folders,
                                                   os.path.basename(os.path.normpath(template_files_folder)))
                    if not os.path.exists(template_folder):
                        os.makedirs(template_folder)

                    helpers.copy_tree(template_files_folder, template_folder)
                    print "Saved Template Files from '"+template_files_folder+"'."

                # Store Locale Folders
                locale_folders = settings.LOCALE_PATHS
                locale_files_folders = os.path.join(target_folder, helpers.LOCALE_PATHS)
                if not os.path.exists(locale_files_folders):
                    os.makedirs(locale_files_folders)

                for locale_files_folder in locale_folders:
                    locale_folder = os.path.join(locale_files_folders,
                                                 os.path.basename(os.path.normpath(locale_files_folder)))
                    if not os.path.exists(locale_folder):
                        os.makedirs(locale_folder)

                    helpers.copy_tree(locale_files_folder, locale_folder)
                    print "Saved Locale Files from '"+locale_files_folder+"'."

                # Create Final ZIP Archive
                helpers.zip_dir(target_folder, os.path.join(backup_dir, dir_time_suffix+'.zip'))

                # Cleanup Temp Folder
                shutil.rmtree(target_folder)

                print "Backup Finished. Archive generated."

                return str(os.path.join(backup_dir, dir_time_suffix+'.zip'))
            finally:
                # Reactivate GeoNode Signals
                print "Reactivating GeoNode Signals..."
                resignals()
                print "...done!"
