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
import re
import sys
import shutil
import hashlib
from logging import Formatter, StreamHandler

import psycopg2
import traceback
import dateutil.parser
import logging
import subprocess

from configparser import ConfigParser

from django.conf import settings
from django.core.management.base import CommandError


MEDIA_ROOT = "uploaded"
STATIC_ROOT = "static_root"
STATICFILES_DIRS = "static_dirs"
TEMPLATE_DIRS = "template_dirs"
LOCALE_PATHS = "locale_dirs"
EXTERNAL_ROOT = "external"
ASSETS_ROOT = "assets"


logger = logging.getLogger(__name__)


def option(parser):
    # Named (optional) arguments
    parser.add_argument("-c", "--config", help="Use custom settings.ini configuration file")


def geoserver_option_list(parser):
    # Named (optional) arguments
    parser.add_argument("--geoserver-data-dir", dest="gs_data_dir", default=None, help="Geoserver data directory")

    parser.add_argument(
        "--dump-geoserver-vector-data",
        dest="dump_gs_vector_data",
        action="store_true",
        default=None,
        help="Dump geoserver vector data",
    )

    parser.add_argument(
        "--no-geoserver-vector-data",
        dest="dump_gs_vector_data",
        action="store_false",
        default=None,
        help="Don't dump geoserver vector data",
    )

    parser.add_argument(
        "--dump-geoserver-raster-data",
        dest="dump_gs_raster_data",
        action="store_true",
        default=None,
        help="Dump geoserver raster data",
    )

    parser.add_argument(
        "--no-geoserver-raster-data",
        dest="dump_gs_raster_data",
        action="store_false",
        default=None,
        help="Don't dump geoserver raster data",
    )


class Config:
    def __init__(self, options: dict):
        def apply_options_override(options):
            def get_option(key, fallback):
                o = options.get(key)
                return o if o is not None else fallback

            self.gs_data_dir = get_option("gs_data_dir", self.gs_data_dir)
            self.gs_dump_vector_data = get_option("dump_gs_vector_data", self.gs_dump_vector_data)
            self.gs_dump_raster_data = get_option("dump_gs_raster_data", self.gs_dump_raster_data)

            # store back overrides as current config (needed for saving it into the backup zip)
            self.config_parser["geoserver"]["datadir"] = self.gs_data_dir
            self.config_parser["geoserver"]["dumpvectordata"] = str(self.gs_dump_vector_data)
            self.config_parser["geoserver"]["dumprasterdata"] = str(self.gs_dump_raster_data)

        def load_settings(config):
            self.pg_dump_cmd = config.get("database", "pgdump")
            self.pg_restore_cmd = config.get("database", "pgrestore")
            self.psql_cmd = config.get("database", "psql", fallback="psql")

            self.gs_data_dir = config.get("geoserver", "datadir")

            self.gs_exclude_file_path = (
                ";".join(config.get("geoserver", "datadir_exclude_file_path").split(","))
                if config.has_option("geoserver", "datadir_exclude_file_path")
                else ""
            )

            self.gs_dump_vector_data = config.getboolean("geoserver", "dumpvectordata")
            self.gs_dump_raster_data = config.getboolean("geoserver", "dumprasterdata")

            self.gs_data_dt_filter = (
                config.get("geoserver", "data_dt_filter").split(" ")
                if config.has_option("geoserver", "data_dt_filter")
                else (None, None)
            )

            self.gs_data_datasetname_filter = (
                config.get("geoserver", "data_datasetname_filter").split(",")
                if config.has_option("geoserver", "data_datasetname_filter")
                else ""
            )

            self.gs_data_datasetname_exclude_filter = (
                config.get("geoserver", "data_datasetname_exclude_filter").split(",")
                if config.has_option("geoserver", "data_datasetname_exclude_filter")
                else ""
            )

            self.app_names = config.get("fixtures", "apps").split(",")
            self.dump_names = config.get("fixtures", "dumps").split(",")

        # Start init code
        settings_path = options.get("config")
        if not settings_path:
            raise CommandError("Missing mandatory option (-c / --config)")
        if not os.path.isabs(settings_path):
            settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, settings_path)
        if not os.path.exists(settings_path):
            raise CommandError(f"Provided '-c' / '--config' file does not exist: {settings_path}")

        self.config_parser = ConfigParser()
        self.config_parser.read(settings_path)

        # set config from file
        load_settings(self.config_parser)
        # override config from command line
        apply_options_override(options)


sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))


def get_db_conn(db_name, db_user, db_port, db_host, db_passwd):
    """Get db conn (GeoNode)"""
    db_host = db_host if db_host is not None else "localhost"
    db_port = db_port if db_port is not None else 5432
    conn = psycopg2.connect(
        f"dbname='{db_name}' user='{db_user}' port='{db_port}' host='{db_host}' password='{db_passwd}'"
    )
    return conn


def get_tables(db_user, db_passwd, db_name, db_host="localhost", db_port=5432):
    select = f"SELECT tablename FROM pg_tables WHERE tableowner = '{db_user}' and schemaname = 'public'"
    logger.info(f"Retrieving table list from DB {db_name}@{db_host}: {select}")

    try:
        conn = get_db_conn(db_name, db_user, db_port, db_host, db_passwd)
        curs = conn.cursor()
        curs.execute(select)
        pg_tables = [table[0] for table in curs.fetchall()]
        conn.commit()
        return pg_tables

    except Exception as e:
        traceback.print_exc()
        raise e
    finally:
        curs.close()
        conn.close()


def truncate_tables(db_name, db_user, db_port, db_host, db_passwd):
    """HARD Truncate all DB Tables"""
    db_host = db_host if db_host is not None else "localhost"
    db_port = db_port if db_port is not None else 5432

    logger.info(f"Truncating the tables in DB {db_name} @{db_host}:{db_port} for user {db_user}")
    pg_tables = get_tables(db_user, db_passwd, db_name, db_host, db_port)
    logger.info(f"Tables found: {pg_tables}")

    conn = get_db_conn(db_name, db_user, db_port, db_host, db_passwd)
    bad_tables = []

    try:
        for table in sorted(pg_tables):
            if table == "br_restoredbackup":
                continue
            logger.info(f"Truncating table : {table}")
            try:
                curs = conn.cursor()
                curs.execute(f"TRUNCATE {table} CASCADE;")
                conn.commit()
            except Exception as e:
                logger.warning(f"Could not truncate table {table}: {e}", exc_info=e)
                bad_tables.append(table)
                conn.rollback()
        if bad_tables:
            raise Exception(f"Could not truncate tables {bad_tables}")

    finally:
        curs.close()
        conn.close()


def dump_db(config, db_name, db_user, db_port, db_host, db_passwd, target_folder):
    """Dump Full DB into target folder"""
    db_host = db_host if db_host is not None else "localhost"
    db_port = db_port if db_port is not None else 5432

    logger.info("Dumping data tables")
    pg_tables = get_tables(db_user, db_passwd, db_name, db_host, db_port)
    logger.info(f"Tables found: {pg_tables}")

    include_filter = config.gs_data_datasetname_filter
    exclude_filter = config.gs_data_datasetname_exclude_filter

    if include_filter:
        filtered_tables = []
        for pat in include_filter:
            filtered_tables += glob_filter(pg_tables, pat)
        pg_tables = filtered_tables
        logger.info(f"Tables found after INCLUDE filtering: {pg_tables}")

    elif exclude_filter:
        for pat in exclude_filter:
            names = glob_filter(pg_tables, pat)
            for exclude_table in names:
                pg_tables.remove(exclude_table)
        logger.info(f"Tables found after EXCLUDE filtering: {pg_tables}")

    logger.debug(f"Cleaning up destination folder {target_folder}...")
    empty_folder(target_folder)
    for table in sorted(pg_tables):
        logger.info(f" - Dumping data table: {db_name}:{table}")
        command = (
            f"{config.pg_dump_cmd} "
            f" -h {db_host} -p {str(db_port)} -U {db_user} -d {db_name} "
            f" -b "
            f" -t '\"{str(table)}\"' "
            f" -f {os.path.join(target_folder, f'{table}.sql ')}"
        )
        ret = subprocess.call(command, shell=True, env={"PGPASSWORD": db_passwd})
        if ret != 0:
            logger.error(f"DUMP FAILED FOR TABLE {table}")


def restore_db(config, db_name, db_user, db_port, db_host, db_passwd, source_folder, preserve_tables):
    """Restore Full DB into target folder"""
    db_host = db_host if db_host is not None else "localhost"
    db_port = db_port if db_port is not None else 5432

    logger.info("Restoring data tables")

    dump_extensions = ["dump", "sql"]
    file_names = [fn for fn in os.listdir(source_folder) if any(fn.endswith(ext) for ext in dump_extensions)]
    for filename in sorted(file_names):
        table_name = os.path.splitext(filename)[0]
        logger.info(f" - restoring data table: {db_name}:{table_name} ")
        if filename.endswith("dump"):
            command = (
                f"{config.pg_restore_cmd} "
                f" -h {db_host} -p {str(db_port)} -d {db_name}"
                f" -U {db_user} --role={db_user} "
                f' -t "{table_name}" '
                f' {"-c" if not preserve_tables else "" } '
                f" {os.path.join(source_folder, filename)} "
            )
            ret = subprocess.call(command, env={"PGPASSWORD": db_passwd}, shell=True)
            if ret:
                logger.error(f"RESTORE FAILED FOR FILE {filename}")

        elif filename.endswith("sql"):
            args = (
                f"{config.psql_cmd} "
                f" -h {db_host} "
                f" -p {str(db_port)} "
                f" -d {db_name} "
                f" -U {db_user} "
                f" -f {os.path.join(source_folder, filename)} "
                " -q -b "
            )
            cproc = subprocess.run(args, env={"PGPASSWORD": db_passwd}, shell=True, capture_output=True, text=True)
            ret = cproc.returncode
            if ret:
                logger.error(f"RESTORE FAILED FOR FILE {filename}")
                logger.error(f'CMD:: {" ".join(args)}')
                # logger.error(f'OUT:: {cproc.stdout}')
                logger.error(f"ERR:: {cproc.stderr}")


def remove_existing_tables(db_name, db_user, db_port, db_host, db_passwd):
    logger.info("Dropping existing GeoServer vector data from DB")
    pg_tables = get_tables(db_user, db_passwd, db_name, db_host, db_port)
    bad_tables = []

    conn = get_db_conn(db_name, db_user, db_port, db_host, db_passwd)

    for table in pg_tables:
        logger.info(f"- Drop Table: {db_name}:{table} ")
        try:
            curs = conn.cursor()
            curs.execute(f'DROP TABLE "{table}" CASCADE')
            conn.commit()
        except Exception as e:
            logger.warning(f"Error Dropping Table {table}: {str(e)}", exc_info=e)
            bad_tables.append(table)
            conn.rollback()

    if bad_tables:
        logger.warning("Some tables could not be removed. This error will probably break the procedure in next steps.")
        logger.warning(f"Bad tables list: {bad_tables}")

    curs.close()
    conn.close()


def confirm(prompt=None, resp=False):
    """prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.

    >>> confirm(prompt='Create Directory?', resp=True)
    Create Directory? [y]|n:
    True
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y:
    False
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: y
    True
    """

    if prompt is None:
        prompt = "Confirm"

    if resp:
        prompt = f"{prompt} [y]|n: "
    else:
        prompt = f"{prompt} [n]|y: "

    while True:
        ans = input(prompt)
        if not ans:
            return resp
        if ans not in {"y", "Y", "n", "N"}:
            print("please enter y or n.")
            continue
        if ans == "y" or ans == "Y":
            return True
        if ans == "n" or ans == "N":
            return False


def md5_file_hash(file_path):
    """
    A method generating MD5 hash of the provided file.

    :param file_path: file's path with an extension, which will be opened for reading and generating md5 hash
    :return: hex representation of md5 hash
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def ignore_time(cmp_operator, iso_date):
    def ignoref(directory, contents):
        if not cmp_operator or not iso_date:
            return []
        _timestamp = dateutil.parser.isoparse(iso_date).timestamp()
        if cmp_operator == "<":
            return (f for f in contents if os.path.getmtime(os.path.join(directory, f)) > _timestamp)
        elif cmp_operator == "<=":
            return (f for f in contents if os.path.getmtime(os.path.join(directory, f)) >= _timestamp)
        elif cmp_operator == "=":
            return (f for f in contents if os.path.getmtime(os.path.join(directory, f)) == _timestamp)
        elif cmp_operator == ">":
            return (f for f in contents if os.path.getmtime(os.path.join(directory, f)) < _timestamp)
        elif cmp_operator == ">=":
            return (f for f in contents if os.path.getmtime(os.path.join(directory, f)) <= _timestamp)

    return ignoref


def glob2re(pat):
    """Translate a shell PATTERN to a regular expression.

    There is no way to quote meta-characters.
    """

    i, n = 0, len(pat)
    res = ""
    while i < n:
        c = pat[i]
        i = i + 1
        if c == "*":
            # res = res + '.*'
            res = f"{res}[^/]*"
        elif c == "?":
            # res = res + '.'
            res = f"{res}[^/]"
        elif c == "[":
            j = i
            if j < n and pat[j] == "!":
                j = j + 1
            if j < n and pat[j] == "]":
                j = j + 1
            while j < n and pat[j] != "]":
                j = j + 1
            if j >= n:
                res = f"{res}\\["
            else:
                stuff = pat[i:j].replace("\\", "\\\\")
                i = j + 1
                if stuff[0] == "!":
                    stuff = f"^{stuff[1:]}"
                elif stuff[0] == "^":
                    stuff = f"\\{stuff}"
                res = f"{res}[{stuff}]"
        else:
            res = res + re.escape(c)
    return f"{res}\\Z(?ms)"


def glob_filter(names, pat):
    return (name for name in names if re.match(glob2re(pat), name))


def empty_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")


def setup_logger():
    if "geonode.br" not in settings.LOGGING["loggers"]:
        settings.LOGGING["formatters"]["br"] = {"format": "%(levelname)-7s %(asctime)s %(message)s"}
        settings.LOGGING["handlers"]["br"] = {"level": "DEBUG", "class": "logging.StreamHandler", "formatter": "br"}
        settings.LOGGING["loggers"]["geonode.br"] = {"handlers": ["br"], "level": "INFO", "propagate": False}

        logger = logging.getLogger("geonode.br")

        handler = StreamHandler()
        handler.setFormatter(Formatter(fmt="%(levelname)-7s %(asctime)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
