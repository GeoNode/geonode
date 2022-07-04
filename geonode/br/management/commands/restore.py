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

import os
import json
import time
import uuid
import shutil
import logging
import zipfile
import requests
import tempfile
import warnings
import traceback
from typing import Union
from datetime import datetime

from .utils import utils

from distutils import dir_util
from requests.auth import HTTPBasicAuth
from urllib.parse import urlparse, urljoin

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
from django.db.utils import IntegrityError
from django_jsonfield_backport.features import extend_features
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    help = 'Restore the GeoNode application data'

    def add_arguments(self, parser):

        # Named (optional) arguments
        utils.option(parser)

        utils.geoserver_option_list(parser)

        parser.add_argument(
            '-i',
            '--ignore-errors',
            action='store_true',
            dest='ignore_errors',
            default=False,
            help='Stop after any errors are encountered.')

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
            dest='skip_geoserver',
            default=False,
            help='Skips geoserver backup')

        parser.add_argument(
            '--skip-geoserver-info',
            action='store_true',
            dest='skip_geoserver_info',
            default=True,
            help='Skips geoserver Global Infos')

        parser.add_argument(
            '--skip-geoserver-security',
            action='store_true',
            dest='skip_geoserver_security',
            default=True,
            help='Skips geoserver Security Settings')

        parser.add_argument(
            '--backup-file',
            dest='backup_file',
            default=None,
            help='Backup archive containing GeoNode data to restore.')

        parser.add_argument(
            '--recovery-file',
            dest='recovery_file',
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
            help="Compares the backup file with restoration logs, and applies it only, if it hasn't been already restored"  # noqa
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

        parser.add_argument(
            '--soft-reset',
            action='store_true',
            dest='soft_reset',
            default=False,
            help='If True, preserve geoserver resources and tables'
        )

    def handle(self, **options):
        extend_features(connection)
        skip_read_only = options.get('skip_read_only')
        config = Configuration.load()

        # activate read only mode and store it's original config value
        if not skip_read_only:
            original_read_only_value = config.read_only
            config.read_only = True
            config.save()

        try:
            self.execute_restore(**options)
        except Exception:
            raise
        finally:
            # restore read only mode's original value
            if not skip_read_only:
                config.read_only = original_read_only_value
                config.save()

    def execute_restore(self, **options):
        self.validate_backup_file_options(**options)
        ignore_errors = options.get('ignore_errors')
        force_exec = options.get('force_exec')
        skip_geoserver = options.get('skip_geoserver')
        skip_geoserver_info = options.get('skip_geoserver_info')
        skip_geoserver_security = options.get('skip_geoserver_security')
        backup_file = options.get('backup_file')
        recovery_file = options.get('recovery_file')
        backup_files_dir = options.get('backup_files_dir')
        with_logs = options.get('with_logs')
        notify = options.get('notify')
        soft_reset = options.get('soft_reset')

        # choose backup_file from backup_files_dir, if --backup-files-dir was provided
        if backup_files_dir:
            backup_file = self.parse_backup_files_dir(backup_files_dir)
        else:
            backup_files_dir = os.path.dirname(backup_file)

        # calculate and validate backup archive hash
        backup_md5 = self.validate_backup_file_hash(backup_file)

        # check if the original backup file ini setting are available or not
        backup_ini = self.check_backup_ini_settings(backup_file)
        if backup_ini:
            options['config'] = backup_ini
        config = utils.Config(options)

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
            # restore_folder must be located in the directory Geoserver has access to (and it should
            # not be Geoserver data dir)
            # for dockerized project-template GeoNode projects, it should be located in /backup-restore,
            # otherwise default tmp directory is chosen
            temp_dir_path = backup_files_dir if os.path.exists(backup_files_dir) else None

            restore_folder = os.path.join(temp_dir_path, f'tmp{str(uuid.uuid4())[:4]}')
            try:
                os.makedirs(restore_folder, exist_ok=True)
            except Exception as e:
                raise e
            try:
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
                    print(f"[Sanity Check] Full Write Access to '{restore_folder}' ...")
                    chmod_tree(restore_folder)
                    print(f"[Sanity Check] Full Write Access to '{media_root}' ...")
                    chmod_tree(media_root)
                    print(f"[Sanity Check] Full Write Access to '{static_root}' ...")
                    chmod_tree(static_root)
                    for static_files_folder in static_folders:
                        print(f"[Sanity Check] Full Write Access to '{static_files_folder}' ...")
                        chmod_tree(static_files_folder)
                    for template_files_folder in template_folders:
                        print(f"[Sanity Check] Full Write Access to '{template_files_folder}' ...")
                        chmod_tree(template_files_folder)
                    for locale_files_folder in locale_folders:
                        print(f"[Sanity Check] Full Write Access to '{locale_files_folder}' ...")
                        chmod_tree(locale_files_folder)
                except Exception as exception:
                    if notify:
                        restore_notification.apply_async(
                            (admin_emails, backup_file, backup_md5, str(exception)))

                    print("...Sanity Checks on Folder failed. Please make sure that the current user has full WRITE access to the above folders (and sub-folders or files).")  # noqa
                    print("Reason:")
                    raise

                if not skip_geoserver:
                    try:
                        print(f"[Sanity Check] Full Write Access to '{target_folder}' ...")
                        chmod_tree(target_folder)
                        self.restore_geoserver_backup(config, settings, target_folder,
                                                      skip_geoserver_info, skip_geoserver_security,
                                                      ignore_errors, soft_reset)
                        self.prepare_geoserver_gwc_config(config, settings)
                        self.restore_geoserver_raster_data(config, settings, target_folder)
                        self.restore_geoserver_vector_data(config, settings, target_folder, soft_reset)
                        print("Restoring geoserver external resources")
                        self.restore_geoserver_externals(config, settings, target_folder)
                    except Exception as exception:
                        if recovery_file:
                            with tempfile.TemporaryDirectory(dir=temp_dir_path) as restore_folder:
                                recovery_folder = extract_archive(recovery_file, restore_folder)
                                self.restore_geoserver_backup(config, settings, recovery_folder,
                                                              skip_geoserver_info, skip_geoserver_security,
                                                              ignore_errors, soft_reset)
                                self.restore_geoserver_raster_data(config, settings, recovery_folder)
                                self.restore_geoserver_vector_data(config, settings, recovery_folder, soft_reset)
                                self.restore_geoserver_externals(config, settings, recovery_folder)
                        if notify:
                            restore_notification.apply_async(
                                (admin_emails, backup_file, backup_md5, str(exception)))
                        raise exception
                else:
                    print("Skipping geoserver backup restore")

                # Prepare Target DB
                try:
                    call_command('makemigrations', interactive=False)
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
                        abortlater = False
                        for app_name, dump_name in zip(config.app_names, config.dump_names):
                            fixture_file = os.path.join(target_folder, f"{dump_name}.json")

                            print(f"Deserializing '{fixture_file}'")
                            try:
                                call_command('loaddata', fixture_file, app_label=app_name)
                            except IntegrityError:
                                traceback.print_exc()
                                logger.warning(f"WARNING: The fixture '{dump_name}' fails on integrity check and import is aborted after all fixtures have been checked.")  # noqa
                                abortlater = True
                            except Exception as e:
                                traceback.print_exc()
                                logger.warning(f"WARNING: No valid fixture data found for '{dump_name}'.")
                                # helpers.load_fixture(app_name, fixture_file)
                                raise e

                        if abortlater:
                            raise IntegrityError()

                        # Restore Media Root
                        if config.gs_data_dt_filter[0] is None:
                            shutil.rmtree(media_root, ignore_errors=True)

                        if not os.path.exists(media_root):
                            os.makedirs(media_root, exist_ok=True)

                        copy_tree(media_folder, media_root)
                        chmod_tree(media_root)
                        print(f"Media Files Restored into '{media_root}'.")

                        # Restore Static Root
                        if config.gs_data_dt_filter[0] is None:
                            shutil.rmtree(static_root, ignore_errors=True)

                        if not os.path.exists(static_root):
                            os.makedirs(static_root, exist_ok=True)

                        copy_tree(static_folder, static_root)
                        chmod_tree(static_root)
                        print(f"Static Root Restored into '{static_root}'.")

                        # Restore Static Folders
                        for static_files_folder in static_folders:

                            # skip restoration of static files of apps not located under LOCAL_ROOT path
                            # (check to prevent overriding files from site-packages
                            #  in project-template based GeoNode projects)
                            if getattr(settings, 'LOCAL_ROOT', None) and \
                                    not static_files_folder.startswith(settings.LOCAL_ROOT):
                                print(
                                    f"Skipping static directory: {static_files_folder}. "
                                    f"It's not located under LOCAL_ROOT path: {settings.LOCAL_ROOT}.")
                                continue

                            if config.gs_data_dt_filter[0] is None:
                                shutil.rmtree(static_files_folder, ignore_errors=True)

                            if not os.path.exists(static_files_folder):
                                os.makedirs(static_files_folder, exist_ok=True)

                            copy_tree(os.path.join(static_files_folders,
                                                   os.path.basename(os.path.normpath(static_files_folder))),
                                      static_files_folder)
                            chmod_tree(static_files_folder)
                            print(f"Static Files Restored into '{static_files_folder}'.")

                        # Restore Template Folders
                        for template_files_folder in template_folders:

                            # skip restoration of template files of apps not located under LOCAL_ROOT path
                            # (check to prevent overriding files from site-packages
                            #  in project-template based GeoNode projects)
                            if getattr(settings, 'LOCAL_ROOT', None) and \
                                    not template_files_folder.startswith(settings.LOCAL_ROOT):
                                print(
                                    f"Skipping template directory: {template_files_folder}. "
                                    f"It's not located under LOCAL_ROOT path: {settings.LOCAL_ROOT}.")
                                continue

                            if config.gs_data_dt_filter[0] is None:
                                shutil.rmtree(template_files_folder, ignore_errors=True)

                            if not os.path.exists(template_files_folder):
                                os.makedirs(template_files_folder, exist_ok=True)

                            copy_tree(os.path.join(template_files_folders,
                                                   os.path.basename(os.path.normpath(template_files_folder))),
                                      template_files_folder)
                            chmod_tree(template_files_folder)
                            print(f"Template Files Restored into '{template_files_folder}'.")

                        # Restore Locale Folders
                        for locale_files_folder in locale_folders:

                            # skip restoration of locale files of apps not located under LOCAL_ROOT path
                            # (check to prevent overriding files from site-packages
                            #  in project-template based GeoNode projects)
                            if getattr(settings, 'LOCAL_ROOT', None) and \
                                    not locale_files_folder.startswith(settings.LOCAL_ROOT):
                                print(
                                    f"Skipping locale directory: {locale_files_folder}. "
                                    f"It's not located under LOCAL_ROOT path: {settings.LOCAL_ROOT}.")
                                continue

                            if config.gs_data_dt_filter[0] is None:
                                shutil.rmtree(locale_files_folder, ignore_errors=True)

                            if not os.path.exists(locale_files_folder):
                                os.makedirs(locale_files_folder, exist_ok=True)

                            copy_tree(os.path.join(locale_files_folders,
                                                   os.path.basename(os.path.normpath(locale_files_folder))),
                                      locale_files_folder)
                            chmod_tree(locale_files_folder)
                            print(f"Locale Files Restored into '{locale_files_folder}'.")

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
                        restore_notification.apply_async(
                            (admin_emails, backup_file, backup_md5, str(exception)))

                finally:
                    call_command('makemigrations', interactive=False)
                    call_command('migrate', interactive=False, fake=True)
                    call_command('sync_geonode_layers', updatepermissions=True, ignore_errors=True)

                if notify:
                    restore_notification.apply_async(
                        (admin_emails, backup_file, backup_md5))

                print("HINT: If you migrated from another site, do not forget to run the command 'migrate_baseurl' to fix Links")  # noqa
                print(
                    " e.g.:  DJANGO_SETTINGS_MODULE=my_geonode.settings python manage.py migrate_baseurl "
                    "--source-address=my-host-dev.geonode.org --target-address=my-host-prod.geonode.org"
                )
                print("Restore finished.")
            finally:
                shutil.rmtree(restore_folder)

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
                backup_file = file if backup_file is None or os.path.getmtime(file) > os.path.getmtime(backup_file) else backup_file  # noqa

        if backup_file is None:
            warnings.warn(
                "Nothing to do. No backup archive found in provided '--backup-file-dir' directory",
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
                    "is older than the last restored backup.",
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
        archive_md5_file = f"{backup_file.rsplit('.', 1)[0]}.md5"

        if os.path.exists(archive_md5_file):
            with open(archive_md5_file) as md5_file:
                original_backup_md5 = md5_file.readline().strip().split(" ")[0]

            if original_backup_md5 != backup_hash:
                raise RuntimeError(
                    'Backup archive integrity failure. MD5 hash of the  archive '
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

    def check_backup_ini_settings(self, backup_file: str) -> str:
        """
        Method checking backup file's original settings availability

        :param backup_file: path to the backup_file
        :return: backup_ini_file_path original settings used by the backup file
        """
        # check if the ini file is in place
        backup_ini_file_path = f"{backup_file.rsplit('.', 1)[0]}.ini"

        if os.path.exists(backup_ini_file_path):
            return backup_ini_file_path

        return None

    def restore_geoserver_backup(self, config, settings, target_folder,
                                 skip_geoserver_info, skip_geoserver_security,
                                 ignore_errors, soft_reset):
        """Restore GeoServer Catalog"""
        url = settings.OGC_SERVER['default']['LOCATION']
        user = settings.OGC_SERVER['default']['USER']
        passwd = settings.OGC_SERVER['default']['PASSWORD']
        geoserver_bk_file = os.path.join(target_folder, 'geoserver_catalog.zip')

        if not os.path.exists(geoserver_bk_file) or not os.access(geoserver_bk_file, os.R_OK):
            raise Exception(f'ERROR: geoserver restore: file "{geoserver_bk_file}" not found.')

        print(f"Restoring 'GeoServer Catalog [{url}]' from '{geoserver_bk_file}'.")

        # Best Effort Restore: 'options': {'option': ['BK_BEST_EFFORT=true']}
        _options = [
            f"BK_PURGE_RESOURCES={'true' if not soft_reset else 'false'}",
            'BK_CLEANUP_TEMP=true',
            f'BK_SKIP_SETTINGS={("true" if skip_geoserver_info else "false")}',
            f'BK_SKIP_SECURITY={("true" if skip_geoserver_security else "false")}',
            'BK_BEST_EFFORT=true',
            f'exclude.file.path={config.gs_exclude_file_path}'
        ]
        data = {'restore': {'archiveFile': geoserver_bk_file,
                            'options': {'option': _options}}}
        headers = {
            'Accept': 'application/json',
            'Content-type': 'application/json'
        }
        r = requests.post(f'{url}rest/br/restore/', data=json.dumps(data),
                          headers=headers, auth=HTTPBasicAuth(user, passwd))
        error_backup = "Could not successfully restore GeoServer catalog [{{}}rest/br/restore/]: {{}} - {{}}"

        if r.status_code in (200, 201, 406):
            try:
                r = requests.get(f'{url}rest/br/restore.json',
                                 headers=headers,
                                 auth=HTTPBasicAuth(user, passwd),
                                 timeout=10)

                if (r.status_code == 200):
                    gs_backup = r.json()
                    _url = urlparse(gs_backup['restores']['restore'][len(gs_backup['restores']['restore']) - 1]['href'])
                    _url = f'{urljoin(url, _url.path)}?{_url.query}'
                    r = requests.get(_url,
                                     headers=headers,
                                     auth=HTTPBasicAuth(user, passwd),
                                     timeout=10)

                    if (r.status_code == 200):
                        gs_backup = r.json()

                if (r.status_code != 200):
                    raise ValueError(error_backup.format(url, r.status_code, r.text))
            except ValueError:
                raise ValueError(error_backup.format(url, r.status_code, r.text))

            gs_bk_exec_id = gs_backup['restore']['execution']['id']
            r = requests.get(f'{url}rest/br/restore/{gs_bk_exec_id}.json',
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
                    r = requests.get(f'{url}rest/br/restore/{gs_bk_exec_id}.json',
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
                        print(f'{gs_bk_exec_status} - {gs_bk_exec_progress}')
                        time.sleep(3)
                    else:
                        raise ValueError(error_backup.format(url, r.status_code, r.text))

                if gs_bk_exec_status != 'COMPLETED':
                    raise ValueError(error_backup.format(url, r.status_code, r.text))

            else:
                raise ValueError(error_backup.format(url, r.status_code, r.text))

        else:
            raise ValueError(error_backup.format(url, r.status_code, r.text))

    def prepare_geoserver_gwc_config(self, config, settings):
        if (config.gs_data_dir):
            # Cleanup '$config.gs_data_dir/gwc-layers'
            gwc_layers_root = os.path.join(config.gs_data_dir, 'gwc-layers')
            if not os.path.isabs(gwc_layers_root):
                gwc_layers_root = os.path.join(settings.PROJECT_ROOT, '..', gwc_layers_root)
            try:
                shutil.rmtree(gwc_layers_root)
                print(f'Cleaned out old GeoServer GWC Layers Config: {gwc_layers_root}')
            except Exception:
                pass
            if not os.path.exists(gwc_layers_root):
                os.makedirs(gwc_layers_root, exist_ok=True)

    def restore_geoserver_raster_data(self, config, settings, target_folder):
        if (config.gs_data_dir):
            if (config.gs_dump_raster_data):
                # Restore '$config.gs_data_dir/geonode'
                gs_data_folder = os.path.join(target_folder, 'gs_data_dir', 'geonode')
                if os.path.exists(gs_data_folder):
                    gs_data_root = os.path.join(config.gs_data_dir, 'geonode')
                    if not os.path.isabs(gs_data_root):
                        gs_data_root = os.path.join(settings.PROJECT_ROOT, '..', gs_data_root)

                    if not os.path.exists(gs_data_root):
                        os.makedirs(gs_data_root, exist_ok=True)

                    copy_tree(gs_data_folder, gs_data_root)
                    print(f"GeoServer Uploaded Raster Data Restored to '{gs_data_root}'.")
                else:
                    print(f"Skipping geoserver raster data restore: directory \"{gs_data_folder}\" not found.")

                # Restore '$config.gs_data_dir/data/geonode'
                gs_data_folder = os.path.join(target_folder, 'gs_data_dir', 'data', 'geonode')
                if os.path.exists(gs_data_folder):
                    gs_data_root = os.path.join(config.gs_data_dir, 'data', 'geonode')
                    if not os.path.isabs(gs_data_root):
                        gs_data_root = os.path.join(settings.PROJECT_ROOT, '..', gs_data_root)

                    if not os.path.exists(gs_data_root):
                        os.makedirs(gs_data_root, exist_ok=True)

                    copy_tree(gs_data_folder, gs_data_root)
                    print(f"GeoServer Uploaded Data Restored to '{gs_data_root}'.")
                else:
                    print(f"Skipping geoserver raster data restore: directory \"{gs_data_folder}\" not found.")

    def restore_geoserver_vector_data(self, config, settings, target_folder, soft_reset):
        """Restore Vectorial Data from DB"""
        if (config.gs_dump_vector_data):

            gs_data_folder = os.path.join(target_folder, 'gs_data_dir', 'geonode')
            if not os.path.exists(gs_data_folder):
                print(f"Skipping geoserver vector data restore: directory \"{gs_data_folder}\" not found.")
                return

            datastore = settings.OGC_SERVER['default']['DATASTORE']
            if (datastore):
                ogc_db_name = settings.DATABASES[datastore]['NAME']
                ogc_db_user = settings.DATABASES[datastore]['USER']
                ogc_db_passwd = settings.DATABASES[datastore]['PASSWORD']
                ogc_db_host = settings.DATABASES[datastore]['HOST']
                ogc_db_port = settings.DATABASES[datastore]['PORT']

                if not soft_reset:
                    utils.remove_existing_tables(ogc_db_name, ogc_db_user, ogc_db_port, ogc_db_host, ogc_db_passwd)

                utils.restore_db(config, ogc_db_name, ogc_db_user, ogc_db_port,
                                 ogc_db_host, ogc_db_passwd, gs_data_folder, soft_reset)

    def restore_geoserver_externals(self, config, settings, target_folder):
        """Restore external references from XML files"""
        external_folder = os.path.join(target_folder, utils.EXTERNAL_ROOT)
        if os.path.exists(external_folder):
            dir_util.copy_tree(external_folder, '/')
