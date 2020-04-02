# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 OSGeo
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

import json
import traceback
import os
import time
import shutil
import zipfile
import requests
import tempfile
import warnings
from typing import Union
from datetime import datetime

from .utils import utils

from distutils import dir_util
from requests.auth import HTTPBasicAuth

from geonode.br.models import RestoredBackup
from geonode.br.tasks import restore_notification
from geonode.utils import (DisableDjangoSignals,
                           copy_tree,
                           extract_archive,
                           chmod_tree)
from geonode.base.models import Configuration

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):

    help = 'Restore the GeoNode application data'

    def add_arguments(self, parser):

        # Named (optional) arguments
        utils.option(parser)

        utils.geoserver_option_list(parser)

        parser.add_argument(
            '-f',
            '--force',
            action='store_true',
            dest='force_exec',
            default=False,
            help='Forces the execution without asking for confirmation.')

        parser.add_argument(
            '--skip-geoserver',
            action='store_true',
            default=False,
            help='Skips geoserver backup')

        parser.add_argument(
            '--backup-file',
            dest='backup_file',
            default=None,
            help='Backup archive containing GeoNode data to restore.')

        parser.add_argument(
            '--backup-files-dir',
            dest='backup_files_dir',
            default=None,
            help="Directory containing GeoNode backups. Restoration procedure will pick "
                 "the newest created/modified backup which wasn't yet restored, and was "
                 "created after creation date of the currently used backup (the newest "
                 "if no backup was yet restored on the GeoNode instance)."
        )

        parser.add_argument(
            '-l',
            '--with-logs',
            action='store_true',
            dest='with_logs',
            default=False,
            help="Compares the backup file with restoration logs, and applies it only, if it hasn't been already restored"
        )

        parser.add_argument(
            '-n',
            '--notify',
            action='store_true',
            dest='notify',
            default=False,
            help="Sends an email notification to the superusers on procedure error or finish."
        )

        parser.add_argument(
            '--skip-read-only',
            action='store_true',
            dest='skip_read_only',
            default=False,
            help='Skips activation of the Read Only mode in restore procedure execution.'
        )

    def handle(self, **options):
        skip_read_only = options.get('skip_read_only')
        config = Configuration.load()

        # activate read only mode and store it's original config value
        if not skip_read_only:
            original_read_only_value = config.read_only
            config.read_only = True
            config.save()

        try:
            self.execute_restore(**options)
        finally:
            # restore read only mode's original value
            if not skip_read_only:
                config.read_only = original_read_only_value
                config.save()

    def execute_restore(self, **options):
        self.validate_backup_file_options(**options)

        config = utils.Config(options)
        force_exec = options.get('force_exec')
        skip_geoserver = options.get('skip_geoserver')
        backup_file = options.get('backup_file')
        backup_files_dir = options.get('backup_files_dir')
        with_logs = options.get('with_logs')
        notify = options.get('notify')

        # choose backup_file from backup_files_dir, if --backup-files-dir was provided
        if backup_files_dir:
            backup_file = self.parse_backup_files_dir(backup_files_dir)
        else:
            backup_files_dir = os.path.dirname(backup_file)

        # calculate and validate backup archive hash
        backup_md5 = self.validate_backup_file_hash(backup_file)

        # check if the backup has already been restored
        if with_logs:
            if RestoredBackup.objects.filter(archive_md5=backup_md5):
                raise RuntimeError(
                    'Backup archive has already been restored. If you want to restore '
                    'this backup anyway, run the script without "-l" argument.'
                )

        # get a list of instance administrators' emails
        admin_emails = []

        if notify:
            admins = get_user_model().objects.filter(is_superuser=True)
            for user in admins:
                if user.email:
                    admin_emails.append(user.email)

        print("Before proceeding with the Restore, please ensure that:")
        print(" 1. The backend (DB or whatever) is accessible and you have rights")
        print(" 2. The GeoServer is up and running and reachable from this machine")
        message = 'WARNING: The restore will overwrite ALL GeoNode data. You want to proceed?'
        if force_exec or utils.confirm(prompt=message, resp=False):

            # Create Target Folder
            # target_folder must be located in the directory Geoserver has access to, for dockerized
            # project-template GeoNode projects, it has to be located in /geoserver_data/data directory
            with tempfile.TemporaryDirectory(dir=backup_files_dir) as restore_folder:

                # Extract ZIP Archive to Target Folder
                target_folder = extract_archive(backup_file, restore_folder)

                # Write Checks
                media_root = settings.MEDIA_ROOT
                media_folder = os.path.join(target_folder, utils.MEDIA_ROOT)
                static_root = settings.STATIC_ROOT
                static_folder = os.path.join(target_folder, utils.STATIC_ROOT)
                static_folders = settings.STATICFILES_DIRS
                static_files_folders = os.path.join(target_folder, utils.STATICFILES_DIRS)
                template_folders = []
                try:
                    template_folders = settings.TEMPLATE_DIRS
                except Exception:
                    try:
                        template_folders = settings.TEMPLATES[0]['DIRS']
                    except Exception:
                        pass
                template_files_folders = os.path.join(target_folder, utils.TEMPLATE_DIRS)
                locale_folders = settings.LOCALE_PATHS
                locale_files_folders = os.path.join(target_folder, utils.LOCALE_PATHS)

                try:
                    print(("[Sanity Check] Full Write Access to '{}' ...".format(media_root)))
                    chmod_tree(media_root)
                    print(("[Sanity Check] Full Write Access to '{}' ...".format(static_root)))
                    chmod_tree(static_root)
                    for static_files_folder in static_folders:
                        print(("[Sanity Check] Full Write Access to '{}' ...".format(static_files_folder)))
                        chmod_tree(static_files_folder)
                    for template_files_folder in template_folders:
                        print(("[Sanity Check] Full Write Access to '{}' ...".format(template_files_folder)))
                        chmod_tree(template_files_folder)
                    for locale_files_folder in locale_folders:
                        print(("[Sanity Check] Full Write Access to '{}' ...".format(locale_files_folder)))
                        chmod_tree(locale_files_folder)
                except Exception as exception:
                    if notify:
                        restore_notification.delay(admin_emails, backup_file, backup_md5, str(exception))

                    print("...Sanity Checks on Folder failed. Please make sure that the current user has full WRITE access to the above folders (and sub-folders or files).")
                    print("Reason:")
                    raise

                if not skip_geoserver:

                    try:
                        self.restore_geoserver_backup(settings, target_folder)
                        self.restore_geoserver_raster_data(config, settings, target_folder)
                        self.restore_geoserver_vector_data(config, settings, target_folder)
                        print("Restoring geoserver external resources")
                        self.restore_geoserver_externals(config, settings, target_folder)

                    except Exception as exception:
                        if notify:
                            restore_notification.delay(admin_emails, backup_file, backup_md5, str(exception))

                        raise exception

                else:
                    print("Skipping geoserver backup restore")

                # Prepare Target DB
                try:
                    call_command('migrate', interactive=False)

                    db_name = settings.DATABASES['default']['NAME']
                    db_user = settings.DATABASES['default']['USER']
                    db_port = settings.DATABASES['default']['PORT']
                    db_host = settings.DATABASES['default']['HOST']
                    db_passwd = settings.DATABASES['default']['PASSWORD']

                    utils.patch_db(db_name, db_user, db_port, db_host, db_passwd, settings.MONITORING_ENABLED)
                except Exception:
                    traceback.print_exc()

                try:
                    # Deactivate GeoNode Signals
                    with DisableDjangoSignals():
                        # Flush DB
                        try:
                            db_name = settings.DATABASES['default']['NAME']
                            db_user = settings.DATABASES['default']['USER']
                            db_port = settings.DATABASES['default']['PORT']
                            db_host = settings.DATABASES['default']['HOST']
                            db_passwd = settings.DATABASES['default']['PASSWORD']

                            utils.flush_db(db_name, db_user, db_port, db_host, db_passwd)
                        except Exception:
                            try:
                                call_command('flush', interactive=False)
                            except Exception:
                                traceback.print_exc()
                                raise

                        # Restore Fixtures
                        for app_name, dump_name in zip(config.app_names, config.dump_names):
                            fixture_file = os.path.join(target_folder, dump_name+'.json')

                            print("Deserializing "+fixture_file)
                            try:
                                call_command('loaddata', fixture_file, app_label=app_name)
                            except Exception:
                                traceback.print_exc()
                                print("WARNING: No valid fixture data found for '"+dump_name+"'.")
                                # helpers.load_fixture(app_name, fixture_file)
                                raise

                        # Restore Media Root
                        try:
                            shutil.rmtree(media_root)
                        except Exception:
                            pass

                        if not os.path.exists(media_root):
                            os.makedirs(media_root)

                        copy_tree(media_folder, media_root)
                        chmod_tree(media_root)
                        print("Media Files Restored into '"+media_root+"'.")

                        # Restore Static Root
                        try:
                            shutil.rmtree(static_root)
                        except Exception:
                            pass

                        if not os.path.exists(static_root):
                            os.makedirs(static_root)

                        copy_tree(static_folder, static_root)
                        chmod_tree(static_root)
                        print("Static Root Restored into '"+static_root+"'.")

                        # Restore Static Root
                        try:
                            shutil.rmtree(static_root)
                        except Exception:
                            pass

                        if not os.path.exists(static_root):
                            os.makedirs(static_root)

                        copy_tree(static_folder, static_root)
                        chmod_tree(static_root)
                        print("Static Root Restored into '"+static_root+"'.")

                        # Restore Static Folders
                        for static_files_folder in static_folders:

                            # skip restoration of static files of apps not located under LOCAL_ROOT path
                            # (check to prevent overriding files from site-packages in project-template based GeoNode projects)
                            if getattr(settings, 'LOCAL_ROOT', None) and not static_files_folder.startswith(settings.LOCAL_ROOT):
                                print(
                                    f"Skipping static directory: {static_files_folder}. It's not located under LOCAL_ROOT path: {settings.LOCAL_ROOT}.")
                                continue

                            try:
                                shutil.rmtree(static_files_folder)
                            except Exception:
                                pass

                            if not os.path.exists(static_files_folder):
                                os.makedirs(static_files_folder)

                            copy_tree(os.path.join(static_files_folders,
                                                   os.path.basename(os.path.normpath(static_files_folder))),
                                      static_files_folder)
                            chmod_tree(static_files_folder)
                            print("Static Files Restored into '"+static_files_folder+"'.")

                        # Restore Template Folders
                        for template_files_folder in template_folders:

                            # skip restoration of template files of apps not located under LOCAL_ROOT path
                            # (check to prevent overriding files from site-packages in project-template based GeoNode projects)
                            if getattr(settings, 'LOCAL_ROOT', None) and not template_files_folder.startswith(settings.LOCAL_ROOT):
                                print(
                                    f"Skipping template directory: {template_files_folder}. It's not located under LOCAL_ROOT path: {settings.LOCAL_ROOT}.")
                                continue

                            try:
                                shutil.rmtree(template_files_folder)
                            except Exception:
                                pass

                            if not os.path.exists(template_files_folder):
                                os.makedirs(template_files_folder)

                            copy_tree(os.path.join(template_files_folders,
                                                   os.path.basename(os.path.normpath(template_files_folder))),
                                      template_files_folder)
                            chmod_tree(template_files_folder)
                            print("Template Files Restored into '"+template_files_folder+"'.")

                        # Restore Locale Folders
                        for locale_files_folder in locale_folders:

                            # skip restoration of locale files of apps not located under LOCAL_ROOT path
                            # (check to prevent overriding files from site-packages in project-template based GeoNode projects)
                            if getattr(settings, 'LOCAL_ROOT', None) and not locale_files_folder.startswith(settings.LOCAL_ROOT):
                                print(
                                    f"Skipping locale directory: {locale_files_folder}. It's not located under LOCAL_ROOT path: {settings.LOCAL_ROOT}.")
                                continue

                            try:
                                shutil.rmtree(locale_files_folder)
                            except Exception:
                                pass

                            if not os.path.exists(locale_files_folder):
                                os.makedirs(locale_files_folder)

                            copy_tree(os.path.join(locale_files_folders,
                                                   os.path.basename(os.path.normpath(locale_files_folder))),
                                      locale_files_folder)
                            chmod_tree(locale_files_folder)
                            print("Locale Files Restored into '"+locale_files_folder+"'.")

                        call_command('collectstatic', interactive=False)

                        # Cleanup DB
                        try:
                            db_name = settings.DATABASES['default']['NAME']
                            db_user = settings.DATABASES['default']['USER']
                            db_port = settings.DATABASES['default']['PORT']
                            db_host = settings.DATABASES['default']['HOST']
                            db_passwd = settings.DATABASES['default']['PASSWORD']

                            utils.cleanup_db(db_name, db_user, db_port, db_host, db_passwd)
                        except Exception:
                            traceback.print_exc()

                    # store backup info
                    restored_backup = RestoredBackup(
                        name=backup_file.rsplit('/', 1)[-1],
                        archive_md5=backup_md5,
                        creation_date=datetime.fromtimestamp(os.path.getmtime(backup_file))
                    )
                    restored_backup.save()

                except Exception as exception:
                    if notify:
                        restore_notification.delay(admin_emails, backup_file, backup_md5, str(exception))

                finally:
                    call_command('migrate', interactive=False, fake=True)

                if notify:
                    restore_notification.delay(admin_emails, backup_file, backup_md5)

                print("HINT: If you migrated from another site, do not forget to run the command 'migrate_baseurl' to fix Links")
                print(
                    " e.g.:  DJANGO_SETTINGS_MODULE=my_geonode.settings python manage.py migrate_baseurl "
                    "--source-address=my-host-dev.geonode.org --target-address=my-host-prod.geonode.org"
                )
                print("Restore finished.")

    def validate_backup_file_options(self, **options) -> None:
        """
        Method validating --backup-file and --backup-files-dir options

        :param options: self.handle() method options
        :raises: Django CommandError, if options violate requirements
        :return: None
        """

        backup_file = options.get('backup_file')
        backup_files_dir = options.get('backup_files_dir')

        if not any([backup_file, backup_files_dir]):
            raise CommandError("Mandatory option (--backup-file|--backup-dir|--backup-files-dir)")

        if all([backup_file, backup_files_dir]):
            raise CommandError("Exclusive option (--backup-file|--backup-dir|--backup-files-dir)")

        if backup_file:
            if not os.path.isfile(backup_file) or not zipfile.is_zipfile(backup_file):
                raise CommandError("Provided '--backup-file' is not a .zip file")

        if backup_files_dir and not os.path.isdir(backup_files_dir):
            raise CommandError("Provided '--backup-files-dir' is not a directory")

    def parse_backup_files_dir(self, backup_files_dir: str) -> Union[str, None]:
        """
        Method picking the Backup Archive to be restored from the Backup Files Directory.
        Only archives created/modified AFTER the last restored dumps are considered.

        :param backup_files_dir: path to the directory containing backup files
        :return: backup file path, if a proper backup archive was found, and None otherwise
        """
        # get the latest modified backup file available in backup directory
        backup_file = None

        for file_name in os.listdir(backup_files_dir):
            file = os.path.join(backup_files_dir, file_name)
            if zipfile.is_zipfile(file):
                backup_file = file if backup_file is None or os.path.getmtime(file) > os.path.getmtime(backup_file) else backup_file

        if backup_file is None:
            warnings.warn(
                f"Nothing to do. No backup archive found in provided '--backup-file-dir' directory",
                RuntimeWarning
            )
            return

        # get the latest restored backup file
        try:
            last_restored_backup = RestoredBackup.objects.latest('restoration_date')
        except RestoredBackup.DoesNotExist:
            # existing if statement - backup_file will be restored, as no backup is currently loaded
            pass
        else:
            # check if the latest modified backup file is younger than the last restored
            if last_restored_backup.creation_date.timestamp() > os.path.getmtime(backup_file):
                warnings.warn(
                    f"Nothing to do. The newest backup file from --backup-files-dir: '{backup_file}' "
                    f"is older than the last restored backup.",
                    RuntimeWarning
                )
                return

        return backup_file

    def validate_backup_file_hash(self, backup_file: str) -> str:
        """
        Method calculating backup file's hash and validating it, if the proper *.md5 file
        exists in the backup_file directory

        :param backup_file: path to the backup_file
        :return: backup_file hash
        """
        # calculate backup file's md5 hash
        backup_hash = utils.md5_file_hash(backup_file)

        # check md5 hash for backup archive, if the md5 file is in place
        archive_md5_file = backup_file.rsplit('.', 1)[0] + '.md5'

        if os.path.exists(archive_md5_file):
            with open(archive_md5_file, 'r') as md5_file:
                original_backup_md5 = md5_file.readline().strip()

            if original_backup_md5 != backup_hash:
                raise RuntimeError(
                    f'Backup archive integrity failure. MD5 hash of the  archive '
                    f'is different from the one provided in {archive_md5_file}'
                )
        else:
            warnings.warn(
                "Backup archive's MD5 file does not exist under expected path. Skipping integrity check.",
                RuntimeWarning
            )
            # sleep for the proper console writing order
            time.sleep(0.1)

        return backup_hash

    def restore_geoserver_backup(self, settings, target_folder):
        """Restore GeoServer Catalog"""
        url = settings.OGC_SERVER['default']['LOCATION']
        user = settings.OGC_SERVER['default']['USER']
        passwd = settings.OGC_SERVER['default']['PASSWORD']
        geoserver_bk_file = os.path.join(target_folder, 'geoserver_catalog.zip')

        if not os.path.exists(geoserver_bk_file):
            print(('Skipping geoserver restore: ' +
                  'file "{}" not found.'.format(geoserver_bk_file)))
            return

        print("Restoring 'GeoServer Catalog ["+url+"]' into '"+geoserver_bk_file+"'.")

        # Best Effort Restore: 'options': {'option': ['BK_BEST_EFFORT=true']}
        data = {'restore': {'archiveFile': geoserver_bk_file, 'options': {}}}
        headers = {
            'Accept': 'application/json',
            'Content-type': 'application/json'
        }
        r = requests.post(url + 'rest/br/restore/', data=json.dumps(data),
                          headers=headers, auth=HTTPBasicAuth(user, passwd))
        error_backup = 'Could not successfully restore GeoServer ' + \
                       'catalog [{}rest/br/restore/]: {} - {}'

        if r.status_code in (200, 201, 406):
            try:
                r = requests.get(url + 'rest/br/restore.json',
                                 headers=headers,
                                 auth=HTTPBasicAuth(user, passwd),
                                 timeout=10)

                if (r.status_code == 200):
                    gs_backup = r.json()
                    _url = gs_backup['restores']['restore'][len(gs_backup['restores']['restore']) - 1]['href']
                    r = requests.get(_url,
                                     headers=headers,
                                     auth=HTTPBasicAuth(user, passwd),
                                     timeout=10)

                    if (r.status_code == 200):
                        gs_backup = r.json()

                if (r.status_code != 200):
                    raise ValueError(error_backup.format(_url, r.status_code, r.text))
            except ValueError:
                raise ValueError(error_backup.format(url, r.status_code, r.text))

            gs_bk_exec_id = gs_backup['restore']['execution']['id']
            r = requests.get(url + 'rest/br/restore/' + str(gs_bk_exec_id) + '.json',
                             headers=headers,
                             auth=HTTPBasicAuth(user, passwd),
                             timeout=10)

            if (r.status_code == 200):
                gs_bk_exec_status = gs_backup['restore']['execution']['status']
                gs_bk_exec_progress = gs_backup['restore']['execution']['progress']
                gs_bk_exec_progress_updated = '0/0'
                while (gs_bk_exec_status != 'COMPLETED' and gs_bk_exec_status != 'FAILED'):
                    if (gs_bk_exec_progress != gs_bk_exec_progress_updated):
                        gs_bk_exec_progress_updated = gs_bk_exec_progress
                    r = requests.get(url + 'rest/br/restore/' + str(gs_bk_exec_id) + '.json',
                                     headers=headers,
                                     auth=HTTPBasicAuth(user, passwd),
                                     timeout=10)

                    if (r.status_code == 200):

                        try:
                            gs_backup = r.json()
                        except ValueError:
                            raise ValueError(error_backup.format(url, r.status_code, r.text))

                        gs_bk_exec_status = gs_backup['restore']['execution']['status']
                        gs_bk_exec_progress = gs_backup['restore']['execution']['progress']
                        print(str(gs_bk_exec_status) + ' - ' + gs_bk_exec_progress)
                        time.sleep(3)
                    else:
                        raise ValueError(error_backup.format(url, r.status_code, r.text))
            else:
                raise ValueError(error_backup.format(url, r.status_code, r.text))

        else:
            raise ValueError(error_backup.format(url, r.status_code, r.text))

    def restore_geoserver_raster_data(self, config, settings, target_folder):
        if (config.gs_data_dir):
            if (config.gs_dump_raster_data):

                gs_data_folder = os.path.join(target_folder, 'gs_data_dir', 'data', 'geonode')
                if not os.path.exists(gs_data_folder):
                    print(('Skipping geoserver raster data restore: ' +
                          'directory "{}" not found.'.format(gs_data_folder)))
                    return

                # Restore '$config.gs_data_dir/data/geonode'
                gs_data_root = os.path.join(config.gs_data_dir, 'data', 'geonode')
                if not os.path.isabs(gs_data_root):
                    gs_data_root = os.path.join(settings.PROJECT_ROOT, '..', gs_data_root)

                try:
                    chmod_tree(gs_data_root)
                except Exception:
                    print('Original GeoServer Data Dir "{}" must be writable by the current user. \
                        Do not forget to copy it first. It will be wiped-out by the Restore procedure!'.format(gs_data_root))
                    raise

                try:
                    shutil.rmtree(gs_data_root)
                    print('Cleaned out old GeoServer Data Dir: ' + gs_data_root)
                except Exception:
                    pass

                if not os.path.exists(gs_data_root):
                    os.makedirs(gs_data_root)

                copy_tree(gs_data_folder, gs_data_root)
                chmod_tree(gs_data_root)
                print("GeoServer Uploaded Data Restored to '"+gs_data_root+"'.")

                # Cleanup '$config.gs_data_dir/gwc-layers'
                gwc_layers_root = os.path.join(config.gs_data_dir, 'gwc-layers')
                if not os.path.isabs(gwc_layers_root):
                    gwc_layers_root = os.path.join(settings.PROJECT_ROOT, '..', gwc_layers_root)

                try:
                    shutil.rmtree(gwc_layers_root)
                    print('Cleaned out old GeoServer GWC Layers Config: ' + gwc_layers_root)
                except Exception:
                    pass

                if not os.path.exists(gwc_layers_root):
                    os.makedirs(gwc_layers_root)

    def restore_geoserver_vector_data(self, config, settings, target_folder):
        """Restore Vectorial Data from DB"""
        if (config.gs_dump_vector_data):

            gs_data_folder = os.path.join(target_folder, 'gs_data_dir', 'data', 'geonode')
            if not os.path.exists(gs_data_folder):
                print(('Skipping geoserver vector data restore: ' +
                      'directory "{}" not found.'.format(gs_data_folder)))
                return

            datastore = settings.OGC_SERVER['default']['DATASTORE']
            if (datastore):
                ogc_db_name = settings.DATABASES[datastore]['NAME']
                ogc_db_user = settings.DATABASES[datastore]['USER']
                ogc_db_passwd = settings.DATABASES[datastore]['PASSWORD']
                ogc_db_host = settings.DATABASES[datastore]['HOST']
                ogc_db_port = settings.DATABASES[datastore]['PORT']

                utils.restore_db(config, ogc_db_name, ogc_db_user, ogc_db_port,
                                 ogc_db_host, ogc_db_passwd, gs_data_folder)

    def restore_geoserver_externals(self, config, settings, target_folder):
        """Restore external references from XML files"""
        external_folder = os.path.join(target_folder, utils.EXTERNAL_ROOT)
        if os.path.exists(external_folder):
            dir_util.copy_tree(external_folder, '/')
