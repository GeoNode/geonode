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
import pathlib
from typing import Union
from datetime import datetime

from .utils import utils

from distutils import dir_util
from requests.auth import HTTPBasicAuth
from urllib.parse import urlparse, urljoin

from geonode.br.models import RestoredBackup
from geonode.br.tasks import restore_notification
from geonode.utils import DisableDjangoSignals, copy_tree, extract_archive, chmod_tree
from geonode.base.models import Configuration

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Restore the GeoNode application data"

    def add_arguments(self, parser):
        # Named (optional) arguments
        utils.option(parser)

        parser.add_argument(
            "--geoserver-data-dir",
            dest="gs_data_dir",
            default=None,
            help="Geoserver data directory")

        parser.add_argument(
            "-i",
            "--ignore-errors",
            action="store_true",
            dest="ignore_errors",
            default=False,
            help="Stop after any errors are encountered.",
        )

        parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            dest="force_exec",
            default=False,
            help="Forces the execution without asking for confirmation.",
        )

        parser.add_argument(
            "--skip-geoserver", action="store_true", dest="skip_geoserver", default=False, help="Skips geoserver backup"
        )

        parser.add_argument(
            "--skip-geoserver-info",
            action="store_true",
            dest="skip_geoserver_info",
            default=True,
            help="Skips geoserver Global Infos",
        )

        parser.add_argument(
            "--skip-geoserver-security",
            action="store_true",
            dest="skip_geoserver_security",
            default=True,
            help="Skips geoserver Security Settings",
        )

        parser.add_argument(
            "--backup-file", dest="backup_file", default=None, help="Backup archive containing GeoNode data to restore."
        )

        parser.add_argument(
            "--recovery-file",
            dest="recovery_file",
            default=None,
            help="Archive that shall be used to restore the original content of GeoNode should the restore fail.",
        )

        parser.add_argument(
            "--backup-files-dir",
            dest="backup_files_dir",
            default=None,
            help="Directory containing GeoNode backups. Restoration procedure will pick "
            "the newest created/modified backup which wasn't yet restored, and was "
            "created after creation date of the currently used backup (the newest "
            "if no backup was yet restored on the GeoNode instance).",
        )

        parser.add_argument(
            "-l",
            "--with-logs",
            action="store_true",
            dest="with_logs",
            default=False,
            help="Compares the backup file with restoration logs, and applies it only, if it hasn't been already restored",  # noqa
        )

        parser.add_argument(
            "-n",
            "--notify",
            action="store_true",
            dest="notify",
            default=False,
            help="Sends an email notification to the superusers on procedure error or finish.",
        )

        parser.add_argument(
            "--skip-read-only",
            action="store_true",
            dest="skip_read_only",
            default=False,
            help="Skips activation of the Read Only mode in restore procedure execution.",
        )

        parser.add_argument(
            "--soft-reset",
            action="store_true",
            dest="soft_reset",
            default=False,
            help="If True, preserve geoserver resources and tables",
        )

        parser.add_argument(
            "--skip-logger-setup",
            action="store_false",
            dest="setup_logger",
            help='Skips setup of the "geonode.br" logger, "br" handler and "br" format if not present in settings',
        )

    def handle(self, **options):
        skip_read_only = options.get("skip_read_only")
        config = Configuration.load()

        # activate read only mode and store its original config value
        if not skip_read_only:
            original_read_only_value = config.read_only
            config.read_only = True
            config.save()

        if options.get("setup_logger"):
            utils.setup_logger()

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
        ignore_errors = options.get("ignore_errors")
        force_exec = options.get("force_exec")
        skip_geoserver = options.get("skip_geoserver")
        skip_geoserver_info = options.get("skip_geoserver_info")
        skip_geoserver_security = options.get("skip_geoserver_security")
        backup_file = options.get("backup_file")
        recovery_file = options.get("recovery_file")
        backup_files_dir = options.get("backup_files_dir")
        with_logs = options.get("with_logs")
        notify = options.get("notify")
        soft_reset = options.get("soft_reset")

        # choose backup_file from backup_files_dir, if --backup-files-dir was provided
        if backup_files_dir:
            logger.info("*** Looking for backup file...")
            backup_file = self.parse_backup_files_dir(backup_files_dir)
        else:
            backup_files_dir = os.path.dirname(backup_file)

        # calculate and validate backup archive hash
        logger.info("*** Validating backup file...")
        backup_md5 = self.validate_backup_file_hash(backup_file)

        # check if the original backup file ini setting is available or not
        backup_ini = self.check_backup_ini_settings(backup_file)
        if backup_ini:
            options["config"] = backup_ini
        config = utils.Config(options)

        # check if the backup has already been restored
        if with_logs:
            if RestoredBackup.objects.filter(archive_md5=backup_md5):
                raise RuntimeError(
                    "Backup archive has already been restored. If you want to restore "
                    'this backup anyway, run the script without "-l" argument.'
                )

        # get a list of instance administrators' emails
        admin_emails = []

        if notify:
            admins = get_user_model().objects.filter(is_superuser=True)
            for user in admins:
                if user.email:
                    admin_emails.append(user.email)

        if not force_exec:
            print("Before proceeding with the Restore, please ensure that:")
            print(" 1. The backend (DB or whatever) is accessible and you have rights")
            print(" 2. The GeoServer is up and running and reachable from this machine")

        message = "WARNING: The restore will overwrite ALL GeoNode data. You want to proceed?"
        if force_exec or utils.confirm(prompt=message, resp=False):
            # Create Target Folder
            # restore_folder must be located in the directory Geoserver has access to (and it should
            # not be Geoserver data dir)
            # for dockerized project-template GeoNode projects, it should be located in /backup-restore,
            # otherwise default tmp directory is chosen
            temp_dir_path = backup_files_dir if os.path.exists(backup_files_dir) else None

            restore_folder = os.path.join(
                temp_dir_path, f"unzip_{pathlib.Path(backup_file).stem}_{str(uuid.uuid4())[:4]}"
            )
            try:
                os.makedirs(restore_folder, exist_ok=True)
            except Exception as e:
                raise e
            try:
                # Extract ZIP Archive to Target Folder
                logger.info("*** Unzipping backup file...")
                target_folder = extract_archive(backup_file, restore_folder)

                # Write Checks
                media_root = settings.MEDIA_ROOT
                media_folder = os.path.join(target_folder, utils.MEDIA_ROOT)
                assets_root = settings.ASSETS_ROOT
                assets_folder = os.path.join(target_folder, utils.ASSETS_ROOT)
                try:
                    logger.info("*** Performing some checks...")
                    logger.info(f"[Sanity Check] Full Write Access to restore folder: '{restore_folder}' ...")
                    chmod_tree(restore_folder)
                    logger.info(f"[Sanity Check] Full Write Access to media root: '{media_root}' ...")
                    chmod_tree(media_root)
                    logger.info(f"[Sanity Check] Full Write Access to assets root: '{assets_root}' ...")
                    chmod_tree(assets_root)
                except Exception as e:
                    if notify:
                        restore_notification.apply_async(
                            args=(admin_emails, backup_file, backup_md5, str(e)), expiration=30
                        )

                    logger.error(
                        "Sanity Checks on Folder failed. "
                        "Please make sure that the current user has full WRITE access to the above folders "
                        "(and sub-folders or files).",
                        exc_info=e,
                    )  # noqa
                    raise Exception(f"Some folders need write access: {str(e)}")

                if not skip_geoserver:
                    try:
                        logger.info(f"[Sanity Check] Full Write Access to target folder: '{target_folder}' ...")
                        chmod_tree(target_folder)
                        self.restore_geoserver_backup(
                            config,
                            settings,
                            target_folder,
                            skip_geoserver_info,
                            skip_geoserver_security,
                            ignore_errors,
                            soft_reset,
                        )
                        self.prepare_geoserver_gwc_config(config, settings)
                        self.restore_geoserver_raster_data(config, settings, target_folder)
                        self.restore_geoserver_vector_data(config, settings, target_folder, soft_reset)
                        self.restore_geoserver_externals(config, settings, target_folder)
                        logger.info("*** Recreate GWC tile layers")
                    except Exception as e:
                        logger.warning(f"*** GeoServer Restore failed: {e}", exc_info=e)
                        if recovery_file:
                            logger.warning("*** Trying to restore from recovery file...")
                            with tempfile.TemporaryDirectory(dir=temp_dir_path) as restore_folder:
                                recovery_folder = extract_archive(recovery_file, restore_folder)
                                self.restore_geoserver_backup(
                                    config,
                                    settings,
                                    recovery_folder,
                                    skip_geoserver_info,
                                    skip_geoserver_security,
                                    ignore_errors,
                                    soft_reset,
                                )
                                self.restore_geoserver_raster_data(config, settings, recovery_folder)
                                self.restore_geoserver_vector_data(config, settings, recovery_folder, soft_reset)
                                self.restore_geoserver_externals(config, settings, recovery_folder)
                        if notify:
                            restore_notification.apply_async(
                                args=(admin_emails, backup_file, backup_md5, str(e)), expiration=30
                            )
                        raise Exception(f"GeoServer restore failed: {e}")
                else:
                    logger.info("*** Skipping geoserver backup restore")

                # Prepare Target DB
                try:
                    logger.info("*** Align the database schema")
                    # call_command('makemigrations', interactive=False)
                    call_command("migrate", interactive=False)
                except Exception as e:
                    logger.warning(f"Error while aligning the db: {e}", exc_info=e)

                try:
                    # Deactivate GeoNode Signals
                    with DisableDjangoSignals():
                        # Flush DB
                        try:
                            db_name = settings.DATABASES["default"]["NAME"]
                            db_user = settings.DATABASES["default"]["USER"]
                            db_port = settings.DATABASES["default"]["PORT"]
                            db_host = settings.DATABASES["default"]["HOST"]
                            db_passwd = settings.DATABASES["default"]["PASSWORD"]

                            utils.truncate_tables(db_name, db_user, db_port, db_host, db_passwd)
                        except Exception:
                            logger.info("Error while truncating tables, trying external task")

                            try:
                                call_command("flush", interactive=False)
                            except Exception as e:
                                logger.warning("Could not cleanup GeoNode tables", exc_info=e)
                                raise Exception("Could not cleanup GeoNode tables")

                        # Restore Fixtures
                        err_cnt = 0

                        logger.info("*** Restoring GeoNode fixtures...")

                        fixtures_folder = os.path.join(target_folder, "fixtures")
                        if not os.path.exists(fixtures_folder):
                            # fixtures folder was introduced on 2024-02; make the restore command lenient about
                            # dumps created without such a folder (this behaviour may be removed in a short while)
                            fixtures_folder = target_folder

                        for app_name, dump_name in zip(config.app_names, config.dump_names):
                            fixture_file = os.path.join(fixtures_folder, f"{dump_name}.json")

                            logger.info(f" - restoring '{fixture_file}'")
                            try:
                                call_command("loaddata", fixture_file, app_label=app_name)
                            except IntegrityError as e:
                                logger.warning(
                                    f"The fixture '{dump_name}' failed the integrity check. "
                                    "Import will be aborted after all fixtures have been checked",
                                    exc_info=e,
                                )  # noqa
                                err_cnt += 1
                            except Exception as e:
                                logger.warning(f"No valid fixture data found for '{dump_name}'", exc_info=e)
                                # helpers.load_fixture(app_name, fixture_file)
                                raise e

                        if err_cnt:
                            raise IntegrityError(f"{err_cnt} fixtures could not be loaded")

                        # Restore Media Root
                        logger.info("*** Restore media root...")
                        self.restore_folder(config, media_root, media_folder)
                        logger.info("*** Restore assets root...")
                        self.restore_folder(config, assets_root, assets_folder)

                        # TODO improve this part, by saving the original asset_root path in a variable, then replace with the new one

                    # store backup info
                    restored_backup = RestoredBackup(
                        name=backup_file.rsplit("/", 1)[-1],
                        archive_md5=backup_md5,
                        creation_date=datetime.fromtimestamp(os.path.getmtime(backup_file)),
                    )
                    restored_backup.save()

                except Exception as e:
                    # exception during geonode db restore (gs has already been restored)
                    if notify:
                        restore_notification.apply_async(
                            args=(admin_emails, backup_file, backup_md5, str(e)), expiration=30
                        )
                    raise Exception(f"GeoNode restore failed: {e}")

                # call_command('makemigrations', interactive=False)
                logger.info("*** Synch db with fake migrations...")
                call_command("migrate", interactive=False, fake=True)

                logger.info("*** Sync layers with GeoServer...")
                call_command("sync_geonode_datasets", updatepermissions=True, ignore_errors=True)

                if notify:
                    restore_notification.apply_async(args=(admin_emails, backup_file, backup_md5), expiration=30)

                logger.info(
                    "HINT: If you migrated from another site, do not forget to run the command 'migrate_baseurl' to fix Links"
                )  # noqa
                logger.info(
                    " e.g.:  DJANGO_SETTINGS_MODULE=my_geonode.settings python manage.py migrate_baseurl "
                    "--source-address=my-host-dev.geonode.org --target-address=my-host-prod.geonode.org"
                )
                logger.info("Restore finished.")
            finally:
                logger.info("*** Final filesystem cleanup ...")
                shutil.rmtree(restore_folder)

    def restore_folder(self, config, root, folder):
        if config.gs_data_dt_filter[0] is None:
            shutil.rmtree(root, ignore_errors=True)

        if not os.path.exists(root):
            os.makedirs(root, exist_ok=True)

        copy_tree(folder, root)
        chmod_tree(root)
        logger.info(f"Files restored into '{root}'.")

    def validate_backup_file_options(self, **options) -> None:
        """
        Method validating --backup-file and --backup-files-dir options

        :param options: self.handle() method options
        :raises: Django CommandError, if options violate requirements
        :return: None
        """

        backup_file = options.get("backup_file")
        backup_files_dir = options.get("backup_files_dir")

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
                backup_file = (
                    file
                    if backup_file is None or os.path.getmtime(file) > os.path.getmtime(backup_file)
                    else backup_file
                )  # noqa

        if backup_file is None:
            warnings.warn(
                "Nothing to do. No backup archive found in provided '--backup-file-dir' directory", RuntimeWarning
            )
            return

        # get the latest restored backup file
        try:
            last_restored_backup = RestoredBackup.objects.latest("restoration_date")
        except RestoredBackup.DoesNotExist:
            # existing if statement - backup_file will be restored, as no backup is currently loaded
            pass
        else:
            # check if the latest modified backup file is younger than the last restored
            if last_restored_backup.creation_date.timestamp() > os.path.getmtime(backup_file):
                warnings.warn(
                    f"Nothing to do. The newest backup file from --backup-files-dir: '{backup_file}' "
                    "is older than the last restored backup.",
                    RuntimeWarning,
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
                    "Backup archive integrity failure. MD5 hash of the  archive "
                    f"is different from the one provided in {archive_md5_file}"
                )
        else:
            warnings.warn(
                "Backup archive's MD5 file does not exist under expected path. Skipping integrity check.",
                RuntimeWarning,
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

    def restore_geoserver_backup(
        self, config, settings, target_folder, skip_geoserver_info, skip_geoserver_security, ignore_errors, soft_reset
    ):
        """Restore GeoServer Catalog"""
        url = settings.OGC_SERVER["default"]["LOCATION"]
        user = settings.OGC_SERVER["default"]["USER"]
        passwd = settings.OGC_SERVER["default"]["PASSWORD"]
        geoserver_bk_file = os.path.join(target_folder, "geoserver_catalog.zip")

        logger.info(f"*** Restoring GeoServer catalog [{url}] from '{geoserver_bk_file}'")

        if not os.path.exists(geoserver_bk_file) or not os.access(geoserver_bk_file, os.R_OK):
            raise Exception(f'ERROR: geoserver restore: file "{geoserver_bk_file}" not found.')

        def bstr(x):
            return "true" if x else "false"

        # Best Effort Restore: 'options': {'option': ['BK_BEST_EFFORT=true']}
        _options = [
            f"BK_PURGE_RESOURCES={bstr(not soft_reset)}",
            "BK_CLEANUP_TEMP=true",
            f"BK_SKIP_SETTINGS={bstr(skip_geoserver_info)}",
            f"BK_SKIP_SECURITY={bstr(skip_geoserver_security)}",
            "BK_BEST_EFFORT=true",
            f"exclude.file.path={config.gs_exclude_file_path}",
        ]
        data = {"restore": {"archiveFile": geoserver_bk_file, "options": {"option": _options}}}
        headers = {"Accept": "application/json", "Content-type": "application/json"}
        r = requests.post(
            f"{url}rest/br/restore/", data=json.dumps(data), headers=headers, auth=HTTPBasicAuth(user, passwd)
        )
        error_backup = "Could not successfully restore GeoServer catalog [{}rest/br/restore/]: {} - {}"

        if r.status_code in (200, 201, 406):
            try:
                r = requests.get(
                    f"{url}rest/br/restore.json", headers=headers, auth=HTTPBasicAuth(user, passwd), timeout=10
                )

                if r.status_code == 200:
                    gs_backup = r.json()
                    _url = urlparse(gs_backup["restores"]["restore"][len(gs_backup["restores"]["restore"]) - 1]["href"])
                    _url = f"{urljoin(url, _url.path)}?{_url.query}"
                    r = requests.get(_url, headers=headers, auth=HTTPBasicAuth(user, passwd), timeout=10)

                    if r.status_code == 200:
                        gs_backup = r.json()

                if r.status_code != 200:
                    raise ValueError(error_backup.format(url, r.status_code, r.text))
            except ValueError:
                raise ValueError(error_backup.format(url, r.status_code, r.text))

            gs_bk_exec_id = gs_backup["restore"]["execution"]["id"]
            r = requests.get(
                f"{url}rest/br/restore/{gs_bk_exec_id}.json",
                headers=headers,
                auth=HTTPBasicAuth(user, passwd),
                timeout=10,
            )

            if r.status_code == 200:
                gs_bk_exec_status = gs_backup["restore"]["execution"]["status"]
                gs_bk_exec_progress = gs_backup["restore"]["execution"]["progress"]
                gs_bk_exec_progress_updated = "0/0"
                while gs_bk_exec_status != "COMPLETED" and gs_bk_exec_status != "FAILED":
                    if gs_bk_exec_progress != gs_bk_exec_progress_updated:
                        gs_bk_exec_progress_updated = gs_bk_exec_progress
                    r = requests.get(
                        f"{url}rest/br/restore/{gs_bk_exec_id}.json",
                        headers=headers,
                        auth=HTTPBasicAuth(user, passwd),
                        timeout=10,
                    )

                    if r.status_code == 200:
                        try:
                            gs_backup = r.json()
                        except ValueError:
                            raise ValueError(error_backup.format(url, r.status_code, r.text))

                        gs_bk_exec_status = gs_backup["restore"]["execution"]["status"]
                        gs_bk_exec_progress = gs_backup["restore"]["execution"]["progress"]
                        logger.info(f"Async restore status: {gs_bk_exec_status} - {gs_bk_exec_progress}")
                        time.sleep(3)
                    else:
                        raise ValueError(error_backup.format(url, r.status_code, r.text))

                if gs_bk_exec_status != "COMPLETED":
                    raise ValueError(error_backup.format(url, r.status_code, r.text))

            else:
                raise ValueError(error_backup.format(url, r.status_code, r.text))

        else:
            raise ValueError(error_backup.format(url, r.status_code, r.text))

    def prepare_geoserver_gwc_config(self, config, settings):
        if config.gs_data_dir:
            logger.info("*** Cleanup old GWC config...")
            # Cleanup '$config.gs_data_dir/gwc-layers'
            gwc_layers_root = os.path.join(config.gs_data_dir, "gwc-layers")
            if not os.path.isabs(gwc_layers_root):
                gwc_layers_root = os.path.join(settings.PROJECT_ROOT, "..", gwc_layers_root)
            try:
                logger.info(f"Cleaning out old GeoServer GWC layers config: {gwc_layers_root}")
                shutil.rmtree(gwc_layers_root)
            except Exception as e:
                logger.info(f"Error while cleaning old GeoServer GWC layers config: {e}")
            if not os.path.exists(gwc_layers_root):
                logger.info(f"Recreating GWC layers dir: {gwc_layers_root}")
                os.makedirs(gwc_layers_root, exist_ok=True)

    def restore_geoserver_raster_data(self, config, settings, target_folder):
        if config.gs_data_dir and config.gs_dump_raster_data:
            logger.info("*** Restore raster data")

            for dest_folder, source_root in (
                (
                    os.path.join(config.gs_data_dir, "geonode"),
                    os.path.join(target_folder, "gs_data_dir", "geonode"),
                ),  # Dump '$config.gs_data_dir/geonode'
                (
                    os.path.join(config.gs_data_dir, "data", "geonode"),
                    os.path.join(target_folder, "gs_data_dir", "data", "geonode"),
                ),  # Dump '$config.gs_data_dir/data/geonode'
            ):
                if os.path.exists(source_root):
                    logger.info(f"Restoring raster data to '{dest_folder}'...")
                    if not os.path.isabs(dest_folder):
                        dest_folder = os.path.join(settings.PROJECT_ROOT, "..", dest_folder)

                    if not os.path.exists(dest_folder):
                        os.makedirs(dest_folder, exist_ok=True)

                    logger.info(f"Copying data from '{source_root}' to '{dest_folder}'...")
                    copy_tree(source_root, dest_folder)
                    logger.info(f"Restored raster data to '{dest_folder}'")
                else:
                    logger.info(f"Skipping raster data directory '{source_root}' because it does not exist")

    def restore_geoserver_vector_data(self, config, settings, target_folder, soft_reset):
        """Restore Vectorial Data from DB"""
        if config.gs_dump_vector_data:
            logger.info("*** Restore vector data")

            gs_data_folder = os.path.join(target_folder, "gs_data_dir", "geonode")
            if not os.path.exists(gs_data_folder):
                logger.info(f'Skipping vector data restore: directory "{gs_data_folder}" not found')
                return
            logger.info(f'Restoring vector data from "{gs_data_folder}" not found')

            datastore_name = settings.OGC_SERVER["default"]["DATASTORE"]
            datastore = settings.DATABASES[datastore_name]
            if datastore_name:
                ogc_db_name = datastore["NAME"]
                ogc_db_user = datastore["USER"]
                ogc_db_passwd = datastore["PASSWORD"]
                ogc_db_host = datastore["HOST"]
                ogc_db_port = datastore["PORT"]

                if not soft_reset:
                    utils.remove_existing_tables(ogc_db_name, ogc_db_user, ogc_db_port, ogc_db_host, ogc_db_passwd)

                utils.restore_db(
                    config,
                    ogc_db_name,
                    ogc_db_user,
                    ogc_db_port,
                    ogc_db_host,
                    ogc_db_passwd,
                    gs_data_folder,
                    soft_reset,
                )

    def restore_geoserver_externals(self, config, settings, target_folder):
        """Restore external references from XML files"""
        logger.info("*** Restoring GeoServer external resources...")
        external_folder = os.path.join(target_folder, utils.EXTERNAL_ROOT)
        if os.path.exists(external_folder):
            dir_util.copy_tree(external_folder, "/")
