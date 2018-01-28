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

from __future__ import with_statement
from contextlib import closing
from zipfile import ZipFile, ZIP_DEFLATED

import traceback
import psycopg2
import ConfigParser
import os
import sys
import time
import shutil

from optparse import make_option

try:
    import json
except ImportError:
    from django.utils import simplejson as json

MEDIA_ROOT = 'uploaded'
STATIC_ROOT = 'static_root'
STATICFILES_DIRS = 'static_dirs'
TEMPLATE_DIRS = 'template_dirs'
LOCALE_PATHS = 'locale_dirs'
EXTERNAL_ROOT = 'external'


class Config(object):

    option = make_option(
        '-c',
        '--config',
        type="string",
        help='Use custom settings.ini configuration file')

    geoserver_option_list = (
        make_option(
            '--geoserver-data-dir',
            dest="gs_data_dir",
            type="string",
            default=None,
            help="Geoserver data directory"),
        make_option(
            '--dump-geoserver-vector-data',
            dest="dump_gs_vector_data",
            action="store_true",
            default=None,
            help="Dump geoserver vector data"),
        make_option(
            '--no-geoserver-vector-data',
            dest="dump_gs_vector_data",
            action="store_false",
            default=None,
            help="Don't dump geoserver vector data"),
        make_option(
            '--dump-geoserver-raster-data',
            dest="dump_gs_raster_data",
            action="store_true",
            default=None,
            help="Dump geoserver raster data"),
        make_option(
            '--no-geoserver-raster-data',
            dest="dump_gs_raster_data",
            action="store_false",
            default=None,
            help="Don't dump geoserver raster data"),
    )

    def __init__(self, options):
        self.load_settings(settings_path=options.get('config'))
        self.load_options(options)

    def load_options(self, options):
        if options.get("gs_data_dir", None):
            self.gs_data_dir = options.get("gs_data_dir")

        if options.get("dump_gs_vector_data", None) is not None:
            self.gs_dump_vector_data = options.get("dump_gs_vector_data")

        if options.get("dump_gs_raster_data", None) is not None:
            self.gs_dump_raster_data = options.get("dump_gs_raster_data")

    def load_settings(self, settings_path=None):

        if not settings_path:
            settings_dir = os.path.abspath(os.path.dirname(__file__))
            settings_path = os.path.join(settings_dir, 'settings.ini')

        config = ConfigParser.ConfigParser()
        config.read(settings_path)

        self.pg_dump_cmd = config.get('database', 'pgdump')
        self.pg_restore_cmd = config.get('database', 'pgrestore')

        self.gs_data_dir = config.get('geoserver', 'datadir')
        self.gs_dump_vector_data = \
            config.getboolean('geoserver', 'dumpvectordata')
        self.gs_dump_raster_data = \
            config.getboolean('geoserver', 'dumprasterdata')

        self.app_names = config.get('fixtures', 'apps').split(',')
        self.dump_names = config.get('fixtures', 'dumps').split(',')
        self.migrations = config.get('fixtures', 'migrations').split(',')
        self.manglers = config.get('fixtures', 'manglers').split(',')


sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))


def get_db_conn(db_name, db_user, db_port, db_host, db_passwd):
    """Get db conn (GeoNode)"""
    db_host = db_host if db_host is not None else 'localhost'
    db_port = db_port if db_port is not None else 5432
    conn = psycopg2.connect(
        "dbname='%s' user='%s' port='%s' host='%s' password='%s'" % (db_name, db_user, db_port, db_host, db_passwd)
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
    except Exception:
        try:
            conn.rollback()
        except:
            pass

        traceback.print_exc()

    conn.commit()


def cleanup_db(db_name, db_user, db_port, db_host, db_passwd):
    """Remove spurious records from GeoNode DB"""
    conn = get_db_conn(db_name, db_user, db_port, db_host, db_passwd)
    curs = conn.cursor()

    try:
        curs.execute("DELETE FROM base_contactrole WHERE resource_id is NULL;")
        curs.execute("DELETE FROM base_link WHERE resource_id is NULL;")
    except Exception:
        try:
            conn.rollback()
        except:
            pass

        traceback.print_exc()

    conn.commit()


def flush_db(db_name, db_user, db_port, db_host, db_passwd):
    """HARD Truncate all DB Tables"""
    db_host = db_host if db_host is not None else 'localhost'
    db_port = db_port if db_port is not None else 5432
    conn = get_db_conn(db_name, db_user, db_port, db_host, db_passwd)
    curs = conn.cursor()

    try:
        sql_dump = """SELECT tablename from pg_tables where tableowner = '%s'""" % (db_user)
        curs.execute(sql_dump)
        pg_tables = curs.fetchall()
        for table in pg_tables:
            print "Flushing Data : " + table[0]
            curs.execute("TRUNCATE " + table[0] + " CASCADE;")

    except Exception:
        try:
            conn.rollback()
        except:
            pass

        traceback.print_exc()

    conn.commit()


def dump_db(config, db_name, db_user, db_port, db_host, db_passwd, target_folder):
    """Dump Full DB into target folder"""
    db_host = db_host if db_host is not None else 'localhost'
    db_port = db_port if db_port is not None else 5432
    conn = get_db_conn(db_name, db_user, db_port, db_host, db_passwd)
    curs = conn.cursor()

    try:
        sql_dump = """SELECT tablename from pg_tables where tableowner = '%s'""" % (db_user)
        curs.execute(sql_dump)
        pg_tables = curs.fetchall()
        for table in pg_tables:
            print "Dumping GeoServer Vectorial Data : " + table[0]
            os.system('PGPASSWORD="' + db_passwd + '" ' + config.pg_dump_cmd + ' -h ' + db_host +
                      ' -p ' + db_port + ' -U ' + db_user + ' -F c -b' +
                      ' -t ' + table[0] + ' -f ' +
                      os.path.join(target_folder, table[0] + '.dump ' + db_name))

    except Exception:
        try:
            conn.rollback()
        except:
            pass

        traceback.print_exc()

    conn.commit()


def restore_db(config, db_name, db_user, db_port, db_host, db_passwd, source_folder):
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
            print "Restoring GeoServer Vectorial Data : " + os.path.splitext(table)[0]
            pg_rstcmd = 'PGPASSWORD="' + db_passwd + '" ' + config.pg_restore_cmd + ' -c -h ' + db_host + \
                        ' -p ' + db_port + ' -U ' + db_user + ' -F c ' + \
                        ' -t ' + table[0] + ' ' + \
                        os.path.join(source_folder, table) + ' -d ' + db_name
            os.system(pg_rstcmd)

    except Exception:
        try:
            conn.rollback()
        except:
            pass

        traceback.print_exc()

    conn.commit()


def load_fixture(apps, fixture_file, mangler=None, basepk=-1, owner="admin", datastore='', siteurl=''):

    fixture = open(fixture_file, 'rb')

    if mangler:
        objects = json.load(fixture, cls=mangler,
                            **{"basepk": basepk, "owner": owner, "datastore": datastore, "siteurl": siteurl})
    else:
        objects = json.load(fixture)

    fixture.close()

    return objects


def get_dir_time_suffix():
    """Returns the name of a folder with the 'now' time as suffix"""
    dirfmt = "%4d-%02d-%02d_%02d%02d%02d"
    now = time.localtime()[0:6]
    dirname = dirfmt % now

    return dirname


def zip_dir(basedir, archivename):
    assert os.path.isdir(basedir)
    with closing(ZipFile(archivename, "w", ZIP_DEFLATED, allowZip64=True)) as z:
        for root, dirs, files in os.walk(basedir):
            # NOTE: ignore empty directories
            for fn in files:
                absfn = os.path.join(root, fn)
                zfn = absfn[len(basedir)+len(os.sep):]  # XXX: relative path
                z.write(absfn, zfn)


def copy_tree(src, dst, symlinks=False, ignore=None):
    try:
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                # shutil.rmtree(d)
                if os.path.exists(d):
                    try:
                        os.remove(d)
                    except:
                        try:
                            shutil.rmtree(d)
                        except:
                            pass
                try:
                    shutil.copytree(s, d, symlinks, ignore)
                except:
                    pass
            else:
                try:
                    shutil.copy2(s, d)
                except:
                    pass
    except Exception:
        traceback.print_exc()


def unzip_file(zip_file, dst):
    target_folder = os.path.join(dst, os.path.splitext(os.path.basename(zip_file))[0])
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    with ZipFile(zip_file, "r", allowZip64=True) as z:
        z.extractall(target_folder)

    return target_folder


def chmod_tree(dst, permissions=0o777):
    for dirpath, dirnames, filenames in os.walk(dst):
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            os.chmod(path, permissions)

        for dirname in dirnames:
            path = os.path.join(dirpath, dirname)
            os.chmod(path, permissions)


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
        prompt = '%s [%s]|%s: ' % (prompt, 'y', 'n')
    else:
        prompt = '%s [%s]|%s: ' % (prompt, 'n', 'y')

    while True:
        ans = raw_input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'n', 'N']:
            print 'please enter y or n.'
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False


def load_class(name):

    components = name.split('.')
    mod = __import__(components[0])

    for comp in components[1:]:
        mod = getattr(mod, comp)

    return mod
