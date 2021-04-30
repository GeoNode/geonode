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

import os
import re
import sys
import shutil
import hashlib
import psycopg2
import traceback
import dateutil.parser
import logging

from configparser import ConfigParser

from django.core.management.base import CommandError


MEDIA_ROOT = 'uploaded'
STATIC_ROOT = 'static_root'
STATICFILES_DIRS = 'static_dirs'
TEMPLATE_DIRS = 'template_dirs'
LOCALE_PATHS = 'locale_dirs'
EXTERNAL_ROOT = 'external'
logger = logging.getLogger(__name__)


def option(parser):

    # Named (optional) arguments
    parser.add_argument(
        '-c',
        '--config',
        help='Use custom settings.ini configuration file')


def geoserver_option_list(parser):

    # Named (optional) arguments
    parser.add_argument(
        '--geoserver-data-dir',
        dest="gs_data_dir",
        default=None,
        help="Geoserver data directory")

    parser.add_argument(
        '--dump-geoserver-vector-data',
        dest="dump_gs_vector_data",
        action="store_true",
        default=None,
        help="Dump geoserver vector data")

    parser.add_argument(
        '--no-geoserver-vector-data',
        dest="dump_gs_vector_data",
        action="store_false",
        default=None,
        help="Don't dump geoserver vector data")

    parser.add_argument(
        '--dump-geoserver-raster-data',
        dest="dump_gs_raster_data",
        action="store_true",
        default=None,
        help="Dump geoserver raster data")

    parser.add_argument(
        '--no-geoserver-raster-data',
        dest="dump_gs_raster_data",
        action="store_false",
        default=None,
        help="Don't dump geoserver raster data")


class Config(object):

    def __init__(self, options):
        self.config_parser = None
        self.load_settings(settings_path=options.get('config'))
        self.load_options(options)

    def load_options(self, options):
        if options.get("gs_data_dir", None):
            self.gs_data_dir = options.get("gs_data_dir")
            if self.config_parser:
                self.config_parser['geoserver']['datadir'] = self.gs_data_dir

        if options.get("dump_gs_vector_data", None) is not None:
            self.gs_dump_vector_data = options.get("dump_gs_vector_data")
            if self.config_parser:
                self.config_parser['geoserver']['dumpvectordata'] = self.gs_dump_vector_data

        if options.get("dump_gs_raster_data", None) is not None:
            self.gs_dump_raster_data = options.get("dump_gs_raster_data")
            if self.config_parser:
                self.config_parser['geoserver']['dumprasterdata'] = self.gs_dump_raster_data

    def load_settings(self, settings_path):

        if not settings_path:
            raise CommandError("Mandatory option (-c / --config)")
        if not os.path.isabs(settings_path):
            settings_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                os.pardir,
                settings_path)
        if not os.path.exists(settings_path):
            raise CommandError("Provided '-c' / '--config' file does not exist.")

        config = ConfigParser()
        config.read(settings_path)

        self.pg_dump_cmd = config.get('database', 'pgdump')
        self.pg_restore_cmd = config.get('database', 'pgrestore')

        self.gs_data_dir = config.get('geoserver', 'datadir')

        if config.has_option('geoserver', 'datadir_exclude_file_path'):
            self.gs_exclude_file_path = \
                ';'.join(config.get('geoserver', 'datadir_exclude_file_path').split(','))
        else:
            self.gs_exclude_file_path = ''

        self.gs_dump_vector_data = \
            config.getboolean('geoserver', 'dumpvectordata')
        self.gs_dump_raster_data = \
            config.getboolean('geoserver', 'dumprasterdata')

        if config.has_option('geoserver', 'data_dt_filter'):
            self.gs_data_dt_filter = \
                config.get('geoserver', 'data_dt_filter').split(' ')
        else:
            self.gs_data_dt_filter = (None, None)

        if config.has_option('geoserver', 'data_layername_filter'):
            self.gs_data_layername_filter = \
                config.get('geoserver', 'data_layername_filter').split(',')
        else:
            self.gs_data_layername_filter = ''

        if config.has_option('geoserver', 'data_layername_exclude_filter'):
            self.gs_data_layername_exclude_filter = \
                config.get('geoserver', 'data_layername_exclude_filter').split(',')
        else:
            self.gs_data_layername_exclude_filter = ''

        self.app_names = config.get('fixtures', 'apps').split(',')
        self.dump_names = config.get('fixtures', 'dumps').split(',')

        self.config_parser = config


sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))


def get_db_conn(db_name, db_user, db_port, db_host, db_passwd):
    """Get db conn (GeoNode)"""
    db_host = db_host if db_host is not None else 'localhost'
    db_port = db_port if db_port is not None else 5432
    conn = psycopg2.connect(
        f"dbname='{db_name}' user='{db_user}' port='{db_port}' host='{db_host}' password='{db_passwd}'"
    )
    return conn


def patch_db(db_name, db_user, db_port, db_host, db_passwd, truncate_monitoring=False):
    """Apply patch to GeoNode DB"""
    conn = get_db_conn(db_name, db_user, db_port, db_host, db_passwd)
    curs = conn.cursor()

    try:
        curs.execute("ALTER TABLE base_contactrole ALTER COLUMN resource_id DROP NOT NULL;")
        curs.execute("ALTER TABLE base_link ALTER COLUMN resource_id DROP NOT NULL;")
        if truncate_monitoring:
            curs.execute("TRUNCATE monitoring_notificationreceiver CASCADE;")
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass

        traceback.print_exc()
    finally:
        curs.close()
        conn.close()


def cleanup_db(db_name, db_user, db_port, db_host, db_passwd):
    """Remove spurious records from GeoNode DB"""
    conn = get_db_conn(db_name, db_user, db_port, db_host, db_passwd)
    curs = conn.cursor()

    try:
        curs.execute("DELETE FROM base_contactrole WHERE resource_id is NULL;")
        curs.execute("DELETE FROM base_link WHERE resource_id is NULL;")
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass

        traceback.print_exc()
    finally:
        curs.close()
        conn.close()


def flush_db(db_name, db_user, db_port, db_host, db_passwd):
    """HARD Truncate all DB Tables"""
    db_host = db_host if db_host is not None else 'localhost'
    db_port = db_port if db_port is not None else 5432
    conn = get_db_conn(db_name, db_user, db_port, db_host, db_passwd)
    curs = conn.cursor()

    try:
        sql_dump = f"""SELECT tablename from pg_tables where tableowner = '{db_user}'"""
        curs.execute(sql_dump)
        pg_tables = curs.fetchall()
        for table in pg_tables:
            if table[0] == 'br_restoredbackup':
                continue
            print(f"Flushing Data : {table[0]}")
            curs.execute(f"TRUNCATE {table[0]} CASCADE;")
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        traceback.print_exc()
    finally:
        curs.close()
        conn.close()


def dump_db(config, db_name, db_user, db_port, db_host, db_passwd, target_folder):
    """Dump Full DB into target folder"""
    db_host = db_host if db_host is not None else 'localhost'
    db_port = db_port if db_port is not None else 5432
    conn = get_db_conn(db_name, db_user, db_port, db_host, db_passwd)
    curs = conn.cursor()

    try:
        sql_dump = f"""SELECT tablename from pg_tables where tableowner = '{db_user}'"""
        curs.execute(sql_dump)
        pg_all_tables = [table[0] for table in curs.fetchall()]
        pg_tables = []
        if config.gs_data_layername_filter:
            for pat in config.gs_data_layername_filter:
                pg_tables += glob_filter(pg_all_tables, pat)
        elif config.gs_data_layername_exclude_filter:
            pg_tables = pg_all_tables
            for pat in config.gs_data_layername_exclude_filter:
                names = ','.join(glob_filter(pg_all_tables, pat))
                for exclude_table in names.split(','):
                    pg_tables.remove(exclude_table)
        else:
            pg_tables = pg_all_tables

        print(f"Dumping existing GeoServer Vectorial Data: {pg_tables}")
        empty_folder(target_folder)
        for table in pg_tables:
            print(f"Dump Table: {db_name}:{table}")
            os.system('PGPASSWORD="' + db_passwd + '" ' + config.pg_dump_cmd + ' -h ' + db_host +
                      ' -p ' + str(db_port) + ' -U ' + db_user + ' -F c -b' +
                      ' -t \'"' + str(table) + '"\' -f ' +
                      os.path.join(target_folder, table + '.dump ' + db_name))
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        traceback.print_exc()
    finally:
        curs.close()
        conn.close()


def restore_db(config, db_name, db_user, db_port, db_host, db_passwd, source_folder, preserve_tables):
    """Restore Full DB into target folder"""
    db_host = db_host if db_host is not None else 'localhost'
    db_port = db_port if db_port is not None else 5432
    conn = get_db_conn(db_name, db_user, db_port, db_host, db_passwd)
    # curs = conn.cursor()

    try:
        included_extenstions = ['dump', 'sql']
        file_names = [fn for fn in os.listdir(source_folder)
                      if any(fn.endswith(ext) for ext in included_extenstions)]
        for table in file_names:
            print(f"Restoring GeoServer Vectorial Data : {db_name}:{os.path.splitext(table)[0]} ")
            pg_rstcmd = 'PGPASSWORD="' + db_passwd + '" ' + config.pg_restore_cmd + ' -h ' + db_host + \
                        ' -p ' + str(db_port) + ' -U ' + db_user + ' --role=' + db_user + \
                        ' -F c -t "' + os.path.splitext(table)[0] + '" ' +\
                        os.path.join(source_folder, table) + ' -d ' + db_name
            pg_rstcmd += " -c" if preserve_tables else ""
            os.system(pg_rstcmd)
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        traceback.print_exc()
    finally:
        conn.close()


def remove_existing_tables(db_name, db_user, db_port, db_host, db_passwd):
    conn = get_db_conn(db_name, db_user, db_port, db_host, db_passwd)
    curs = conn.cursor()
    table_list = f"""SELECT tablename from pg_tables where tableowner = '{db_user}'"""

    try:
        curs.execute(table_list)
        pg_all_tables = [table[0] for table in curs.fetchall()]
        print(f"Dropping existing GeoServer Vectorial Data: {table_list}")
        for pg_table in pg_all_tables:
            print(f"Drop Table: {db_name}:{pg_table} ")
            try:
                curs.execute(f"DROP TABLE \"{pg_table}\" CASCADE")
            except Exception as e:
                print(f"Error Droping Table: {e}")
        conn.commit()
    except Exception as e:
        print(f"Error Removing GeoServer Vectorial Data Tables: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        traceback.print_exc()
    finally:
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
        prompt = 'Confirm'

    if resp:
        prompt = f'{prompt} [y]|n: '
    else:
        prompt = f'{prompt} [n]|y: '

    while True:
        ans = input(prompt)
        if not ans:
            return resp
        if ans not in {'y', 'Y', 'n', 'N'}:
            print('please enter y or n.')
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
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
        if cmp_operator == '<':
            return (f for f in contents if os.path.getmtime(os.path.join(directory, f)) > _timestamp)
        elif cmp_operator == '<=':
            return (f for f in contents if os.path.getmtime(os.path.join(directory, f)) >= _timestamp)
        elif cmp_operator == '=':
            return (f for f in contents if os.path.getmtime(os.path.join(directory, f)) == _timestamp)
        elif cmp_operator == '>':
            return (f for f in contents if os.path.getmtime(os.path.join(directory, f)) < _timestamp)
        elif cmp_operator == '>=':
            return (f for f in contents if os.path.getmtime(os.path.join(directory, f)) <= _timestamp)
    return ignoref


def glob2re(pat):
    """Translate a shell PATTERN to a regular expression.

    There is no way to quote meta-characters.
    """

    i, n = 0, len(pat)
    res = ''
    while i < n:
        c = pat[i]
        i = i+1
        if c == '*':
            # res = res + '.*'
            res = f"{res}[^/]*"
        elif c == '?':
            # res = res + '.'
            res = f"{res}[^/]"
        elif c == '[':
            j = i
            if j < n and pat[j] == '!':
                j = j+1
            if j < n and pat[j] == ']':
                j = j+1
            while j < n and pat[j] != ']':
                j = j+1
            if j >= n:
                res = f"{res}\\["
            else:
                stuff = pat[i:j].replace('\\', '\\\\')
                i = j+1
                if stuff[0] == '!':
                    stuff = f"^{stuff[1:]}"
                elif stuff[0] == '^':
                    stuff = f"\\{stuff}"
                res = f'{res}[{stuff}]'
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
            print(f'Failed to delete {file_path}. Reason: {e}')
