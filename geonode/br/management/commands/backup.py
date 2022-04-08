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
import os
import time
import shutil
import requests
import re
import logging

from .utils import utils

from requests.auth import HTTPBasicAuth
from xmltodict import parse as parse_xml
from urllib.parse import urlparse, urljoin

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from django_jsonfield_backport.features import extend_features
from django.db import connection

from geonode.utils import (DisableDjangoSignals,
                           get_dir_time_suffix,
                           zip_dir,
                           copy_tree)

from geonode.base.models import Configuration


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    help = 'Backup the GeoNode application data'

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
            default=False,
            help='Skips geoserver backup')

        parser.add_argument(
            '--backup-dir',
            dest='backup_dir',
            help='Destination folder where to store the backup archive. It must be writable.')

        parser.add_argument(
            '--skip-read-only',
            action='store_true',
            dest='skip_read_only',
            default=False,
            help='Skips activation of the Read Only mode in backup procedure execution.'
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
            # execute backup procedure
            self.execute_backup(**options)
        except Exception:
            raise
        finally:
            # restore read only mode's original value
            if not skip_read_only:
                config.read_only = original_read_only_value
                config.save()

    def execute_backup(self, **options):
        ignore_errors = options.get('ignore_errors')
        config = utils.Config(options)
        force_exec = options.get('force_exec')
        backup_dir = options.get('backup_dir')
        skip_geoserver = options.get('skip_geoserver')

        if not backup_dir or len(backup_dir) == 0:
            raise CommandError("Destination folder '--backup-dir' is mandatory")

        print("Before proceeding with the Backup, please ensure that:")
        print(" 1. The backend (DB or whatever) is accessible and you have rights")
        print(" 2. The GeoServer is up and running and reachable from this machine")
        message = 'You want to proceed?'

        if force_exec or utils.confirm(prompt=message, resp=False):

            # Create Target Folder
            dir_time_suffix = get_dir_time_suffix()
            target_folder = os.path.join(backup_dir, dir_time_suffix)
            if not os.path.exists(target_folder):
                os.makedirs(target_folder, exist_ok=True)
            # Temporary folder to store backup files. It will be deleted at the end.
            os.chmod(target_folder, 0o777)

            if not skip_geoserver:
                self.create_geoserver_backup(config, settings, target_folder, ignore_errors)
                self.dump_geoserver_raster_data(config, settings, target_folder)
                self.dump_geoserver_vector_data(config, settings, target_folder)
                logger.info("Dumping geoserver external resources")
                self.dump_geoserver_externals(config, settings, target_folder)
            else:
                print("Skipping geoserver backup")

            # Deactivate GeoNode Signals
            with DisableDjangoSignals():

                # Dump Fixtures
                for app_name, dump_name in zip(config.app_names, config.dump_names):
                    # prevent dumping BackupRestore application
                    if app_name == 'br':
                        continue

                    logger.info(f"Dumping '{app_name}' into '{dump_name}.json'.")
                    # Point stdout at a file for dumping data to.
                    with open(os.path.join(target_folder, f'{dump_name}.json'), 'w') as output:
                        call_command('dumpdata', app_name, format='json', indent=2, stdout=output)

                # Store Media Root
                media_root = settings.MEDIA_ROOT
                media_folder = os.path.join(target_folder, utils.MEDIA_ROOT)
                if not os.path.exists(media_folder):
                    os.makedirs(media_folder, exist_ok=True)

                copy_tree(media_root, media_folder,
                          ignore=utils.ignore_time(config.gs_data_dt_filter[0], config.gs_data_dt_filter[1]))
                print(f"Saved Media Files from '{media_root}'.")

                # Store Static Root
                static_root = settings.STATIC_ROOT
                static_folder = os.path.join(target_folder, utils.STATIC_ROOT)
                if not os.path.exists(static_folder):
                    os.makedirs(static_folder, exist_ok=True)

                copy_tree(static_root, static_folder,
                          ignore=utils.ignore_time(config.gs_data_dt_filter[0], config.gs_data_dt_filter[1]))
                print(f"Saved Static Root from '{static_root}'.")

                # Store Static Folders
                static_folders = settings.STATICFILES_DIRS
                static_files_folders = os.path.join(target_folder, utils.STATICFILES_DIRS)
                if not os.path.exists(static_files_folders):
                    os.makedirs(static_files_folders, exist_ok=True)

                for static_files_folder in static_folders:

                    # skip dumping of static files of apps not located under LOCAL_ROOT path
                    # (check to prevent saving files from site-packages in project-template based GeoNode projects)
                    if getattr(settings, 'LOCAL_ROOT', None) and \
                            not static_files_folder.startswith(settings.LOCAL_ROOT):
                        print(f"Skipping static directory: {static_files_folder}. "
                              f"It's not located under LOCAL_ROOT path: {settings.LOCAL_ROOT}.")
                        continue

                    static_folder = os.path.join(static_files_folders,
                                                 os.path.basename(os.path.normpath(static_files_folder)))
                    if not os.path.exists(static_folder):
                        os.makedirs(static_folder, exist_ok=True)

                    copy_tree(static_files_folder, static_folder,
                              ignore=utils.ignore_time(config.gs_data_dt_filter[0], config.gs_data_dt_filter[1]))
                    print(f"Saved Static Files from '{static_files_folder}'.")

                # Store Template Folders
                template_folders = []
                try:
                    template_folders = settings.TEMPLATE_DIRS
                except Exception:
                    try:
                        template_folders = settings.TEMPLATES[0]['DIRS']
                    except Exception:
                        pass
                template_files_folders = os.path.join(target_folder, utils.TEMPLATE_DIRS)
                if not os.path.exists(template_files_folders):
                    os.makedirs(template_files_folders, exist_ok=True)

                for template_files_folder in template_folders:

                    # skip dumping of template files of apps not located under LOCAL_ROOT path
                    # (check to prevent saving files from site-packages in project-template based GeoNode projects)
                    if getattr(settings, 'LOCAL_ROOT', None) and \
                            not template_files_folder.startswith(settings.LOCAL_ROOT):
                        print(f"Skipping template directory: {template_files_folder}. "
                              f"It's not located under LOCAL_ROOT path: {settings.LOCAL_ROOT}.")
                        continue

                    template_folder = os.path.join(template_files_folders,
                                                   os.path.basename(os.path.normpath(template_files_folder)))
                    if not os.path.exists(template_folder):
                        os.makedirs(template_folder, exist_ok=True)

                    copy_tree(template_files_folder, template_folder,
                              ignore=utils.ignore_time(config.gs_data_dt_filter[0], config.gs_data_dt_filter[1]))
                    print(f"Saved Template Files from '{template_files_folder}'.")

                # Store Locale Folders
                locale_folders = settings.LOCALE_PATHS
                locale_files_folders = os.path.join(target_folder, utils.LOCALE_PATHS)
                if not os.path.exists(locale_files_folders):
                    os.makedirs(locale_files_folders, exist_ok=True)

                for locale_files_folder in locale_folders:

                    # skip dumping of locale files of apps not located under LOCAL_ROOT path
                    # (check to prevent saving files from site-packages in project-template based GeoNode projects)
                    if getattr(settings, 'LOCAL_ROOT', None) and \
                            not locale_files_folder.startswith(settings.LOCAL_ROOT):
                        logger.info(f"Skipping locale directory: {locale_files_folder}. "
                                    f"It's not located under LOCAL_ROOT path: {settings.LOCAL_ROOT}.")
                        continue

                    locale_folder = os.path.join(locale_files_folders,
                                                 os.path.basename(os.path.normpath(locale_files_folder)))
                    if not os.path.exists(locale_folder):
                        os.makedirs(locale_folder, exist_ok=True)

                    copy_tree(locale_files_folder, locale_folder,
                              ignore=utils.ignore_time(config.gs_data_dt_filter[0], config.gs_data_dt_filter[1]))
                    logger.info(f"Saved Locale Files from '{locale_files_folder}'.")

                # Create Final ZIP Archive
                backup_archive = os.path.join(backup_dir, f'{dir_time_suffix}.zip')
                zip_dir(target_folder, backup_archive)

                # Generate a md5 hash of a backup archive and save it
                backup_md5_file = os.path.join(backup_dir, f'{dir_time_suffix}.md5')
                zip_archive_md5 = utils.md5_file_hash(backup_archive)
                with open(backup_md5_file, 'w') as md5_file:
                    md5_file.write(zip_archive_md5)

                # Generate the ini file with the current settings used by the backup command
                backup_ini_file = os.path.join(backup_dir, f'{dir_time_suffix}.ini')
                with open(backup_ini_file, 'w') as configfile:
                    config.config_parser.write(configfile)

                # Clean-up Temp Folder
                try:
                    shutil.rmtree(target_folder)
                except Exception:
                    logger.warning(f"WARNING: Could not be possible to delete the temp folder: '{target_folder}'")

                print("Backup Finished. Archive generated.")

                return str(os.path.join(backup_dir, f'{dir_time_suffix}.zip'))

    def create_geoserver_backup(self, config, settings, target_folder, ignore_errors):
        # Create GeoServer Backup
        url = settings.OGC_SERVER['default']['LOCATION']
        user = settings.OGC_SERVER['default']['USER']
        passwd = settings.OGC_SERVER['default']['PASSWORD']
        geoserver_bk_file = os.path.join(target_folder, 'geoserver_catalog.zip')

        logger.info(f"Dumping 'GeoServer Catalog [{url}]' into '{geoserver_bk_file}'.")
        r = requests.put(f'{url}rest/reset/',
                         auth=HTTPBasicAuth(user, passwd))
        if r.status_code != 200:
            raise ValueError('Could not reset GeoServer catalog!')
        r = requests.put(f'{url}rest/reload/',
                         auth=HTTPBasicAuth(user, passwd))
        if r.status_code != 200:
            raise ValueError('Could not reload GeoServer catalog!')

        error_backup = "Could not successfully backup GeoServer catalog [{{}}rest/br/backup/]: {{}} - {{}}"

        _options = [
            'BK_CLEANUP_TEMP=true',
            'BK_SKIP_SETTINGS=false',
            'BK_SKIP_SECURITY=false',
            f'BK_BEST_EFFORT={("true" if ignore_errors else "false")}',
            f'exclude.file.path={config.gs_exclude_file_path}'
        ]
        data = {'backup': {'archiveFile': geoserver_bk_file, 'overwrite': 'true',
                           'options': {'option': _options}}}
        headers = {
            'Accept': 'application/json',
            'Content-type': 'application/json'
        }
        r = requests.post(f'{url}rest/br/backup/', data=json.dumps(data),
                          headers=headers, auth=HTTPBasicAuth(user, passwd))

        if r.status_code in (200, 201, 406):
            try:
                r = requests.get(f'{url}rest/br/backup.json',
                                 headers=headers,
                                 auth=HTTPBasicAuth(user, passwd),
                                 timeout=10)
                if (r.status_code == 200):
                    gs_backup = r.json()
                    _url = urlparse(gs_backup['backups']['backup'][len(gs_backup['backups']['backup']) - 1]['href'])
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

            gs_bk_exec_id = gs_backup['backup']['execution']['id']
            r = requests.get(f'{url}rest/br/backup/{gs_bk_exec_id}.json',
                             headers=headers,
                             auth=HTTPBasicAuth(user, passwd),
                             timeout=10)
            if (r.status_code == 200):
                gs_bk_exec_status = gs_backup['backup']['execution']['status']
                gs_bk_exec_progress = gs_backup['backup']['execution']['progress']
                gs_bk_exec_progress_updated = '0/0'
                while (gs_bk_exec_status != 'COMPLETED' and gs_bk_exec_status != 'FAILED'):
                    if (gs_bk_exec_progress != gs_bk_exec_progress_updated):
                        gs_bk_exec_progress_updated = gs_bk_exec_progress
                    r = requests.get(f'{url}rest/br/backup/{gs_bk_exec_id}.json',
                                     headers=headers,
                                     auth=HTTPBasicAuth(user, passwd),
                                     timeout=10)
                    if (r.status_code == 200):

                        try:
                            gs_backup = r.json()
                        except ValueError:
                            raise ValueError(error_backup.format(url, r.status_code, r.text))

                        gs_bk_exec_status = gs_backup['backup']['execution']['status']
                        gs_bk_exec_progress = gs_backup['backup']['execution']['progress']
                        print(f'{gs_bk_exec_status} - {gs_bk_exec_progress}')
                        time.sleep(3)
                    else:
                        raise ValueError(error_backup.format(url, r.status_code, r.text))

                if gs_bk_exec_status == 'FAILED':
                    raise ValueError(error_backup.format(url, r.status_code, r.text))
                _permissions = 0o777
                os.chmod(geoserver_bk_file, _permissions)
                status = os.stat(geoserver_bk_file)
                if oct(status.st_mode & 0o777) != str(oct(_permissions)):
                    raise Exception(f"Could not update permissions of {geoserver_bk_file}")
            else:
                raise ValueError(error_backup.format(url, r.status_code, r.text))

    def dump_geoserver_raster_data(self, config, settings, target_folder):
        if (config.gs_data_dir):
            if (config.gs_dump_raster_data):
                # Dump '$config.gs_data_dir/geonode'
                gs_data_root = os.path.join(config.gs_data_dir, 'geonode')
                if not os.path.isabs(gs_data_root):
                    gs_data_root = os.path.join(settings.PROJECT_ROOT, '..', gs_data_root)
                logger.info(f"Dumping GeoServer Uploaded Data from '{gs_data_root}'.")
                if os.path.exists(gs_data_root):
                    gs_data_folder = os.path.join(target_folder, 'gs_data_dir', 'geonode')
                    if not os.path.exists(gs_data_folder):
                        os.makedirs(gs_data_folder, exist_ok=True)
                    copy_tree(gs_data_root, gs_data_folder,
                              ignore=utils.ignore_time(config.gs_data_dt_filter[0], config.gs_data_dt_filter[1]))
                    logger.info(f"Dumped GeoServer Uploaded Data from '{gs_data_root}'.")
                else:
                    logger.info(f"Skipped GeoServer Uploaded Data '{gs_data_root}'.")

                # Dump '$config.gs_data_dir/data/geonode'
                gs_data_root = os.path.join(config.gs_data_dir, 'data', 'geonode')
                if not os.path.isabs(gs_data_root):
                    gs_data_root = os.path.join(settings.PROJECT_ROOT, '..', gs_data_root)
                logger.info(f"Dumping GeoServer Uploaded Data from '{gs_data_root}'.")
                if os.path.exists(gs_data_root):
                    gs_data_folder = os.path.join(target_folder, 'gs_data_dir', 'data', 'geonode')
                    if not os.path.exists(gs_data_folder):
                        os.makedirs(gs_data_folder, exist_ok=True)

                    copy_tree(gs_data_root, gs_data_folder,
                              ignore=utils.ignore_time(config.gs_data_dt_filter[0], config.gs_data_dt_filter[1]))
                    logger.info(f"Dumped GeoServer Uploaded Data from '{gs_data_root}'.")
                else:
                    logger.info(f"Skipped GeoServer Uploaded Data '{gs_data_root}'.")

    def dump_geoserver_vector_data(self, config, settings, target_folder):
        if (config.gs_dump_vector_data):
            # Dump Vectorial Data from DB
            datastore = settings.OGC_SERVER['default']['DATASTORE']
            if (datastore):
                ogc_db_name = settings.DATABASES[datastore]['NAME']
                ogc_db_user = settings.DATABASES[datastore]['USER']
                ogc_db_passwd = settings.DATABASES[datastore]['PASSWORD']
                ogc_db_host = settings.DATABASES[datastore]['HOST']
                ogc_db_port = settings.DATABASES[datastore]['PORT']

                gs_data_folder = os.path.join(target_folder, 'gs_data_dir', 'geonode')
                if not os.path.exists(gs_data_folder):
                    os.makedirs(gs_data_folder, exist_ok=True)

                utils.dump_db(config, ogc_db_name, ogc_db_user, ogc_db_port,
                              ogc_db_host, ogc_db_passwd, gs_data_folder)

    def dump_geoserver_externals(self, config, settings, target_folder):
        """Scan layers xml and see if there are external references.

        Find references to data outside data dir and include them in
        backup. Also, some references may point to specific url, which
        may not be available later.
        """
        external_folder = os.path.join(target_folder, utils.EXTERNAL_ROOT)

        def copy_external_resource(abspath):
            external_path = os.path.join(external_folder, abspath[1:])
            external_dir = os.path.dirname(external_path)

            if not os.path.isdir(external_dir):
                os.makedirs(external_dir, exist_ok=True)

            try:
                if not os.path.isdir(external_path) and os.path.exists(external_path):
                    shutil.copy2(abspath, external_path)
            except shutil.SameFileError:
                logger.warning(f"WARNING: {abspath} and {external_path} are the same file!")

        def match_filename(key, text, regexp=re.compile("^(.+)$")):
            if key in ('filename', ):
                match = regexp.match(text.decode("utf-8"))
                if match:
                    relpath = match.group(1)
                    try:
                        abspath = relpath if os.path.isabs(relpath) else \
                            os.path.abspath(
                                os.path.join(os.path.dirname(path), relpath))
                        if os.path.exists(abspath):
                            return abspath
                    except Exception:
                        logger.warning(f"WARNING: Error while trying to dump {text}")
                        return

        def match_fileurl(key, text, regexp=re.compile("^file:(.+)$")):
            if key in ('url', ):
                match = regexp.match(text.decode("utf-8"))
                if match:
                    relpath = match.group(1)
                    try:
                        abspath = relpath if os.path.isabs(relpath) else \
                            os.path.abspath(
                                os.path.join(config.gs_data_dir, relpath))
                        if os.path.exists(abspath):
                            return abspath
                    except Exception:
                        logger.warning(f"WARNING: Error while trying to dump {text}")
                        return

        def dump_external_resources_from_xml(path):

            def find_external(tree, key=None):
                if isinstance(tree, dict):
                    for key, value in tree.items():
                        for found in find_external(value, key=key):
                            yield found
                elif isinstance(tree, list):
                    for item in tree:
                        for found in find_external(item, key=key):
                            yield found
                elif isinstance(tree, str):
                    text = tree.encode('utf-8')
                    for find in (match_fileurl, match_filename):
                        found = find(key, text)
                        if found:
                            yield found

            with open(path, 'rb') as fd:
                content = fd.read()
                tree = parse_xml(content)
                for found in find_external(tree):
                    if found.find(config.gs_data_dir) != 0:
                        copy_external_resource(found)

        def is_xml_file(filename, regexp=re.compile(".*.xml$")):
            return regexp.match(filename) is not None

        for directory in ('workspaces', 'styles'):
            source = os.path.join(config.gs_data_dir, directory)
            for root, dirs, files in os.walk(source):
                for filename in filter(is_xml_file, files):
                    path = os.path.join(root, filename)
                    dump_external_resources_from_xml(path)
