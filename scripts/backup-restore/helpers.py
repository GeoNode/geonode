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

from __future__ import with_statement
from contextlib import closing
from zipfile import ZipFile, ZIP_DEFLATED

import traceback
import psycopg2
import ConfigParser
import os
import time
import shutil

import json
import re

MEDIA_ROOT       = 'uploaded'
STATIC_ROOT      = 'static_root'
STATICFILES_DIRS = 'static_dirs'
TEMPLATE_DIRS    = 'template_dirs'
LOCALE_PATHS     = 'locale_dirs'

config = ConfigParser.ConfigParser()
config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'settings.ini'))

db_name   = config.get('targetdb', 'dbname')
db_host   = config.get('targetdb', 'host')
db_port   = config.get('targetdb', 'port') 
db_user   = config.get('targetdb', 'user')
db_passwd = config.get('targetdb', 'passwd')

app_names = config.get('fixtures', 'apps').split(',')
dump_names= config.get('fixtures', 'dumps').split(',')
migrations= config.get('fixtures', 'migrations').split(',')
manglers  = config.get('fixtures', 'manglers').split(',')


def get_db_conn():
    """Get db conn (GeoNode)"""
    conn = psycopg2.connect(
        "dbname='%s' user='%s' port='%s' host='%s' password='%s'" % (db_name, db_user, db_port, db_host, db_passwd)
    )
    return conn


def patch_db():
   """Apply patch to GeoNode DB"""
   conn   = get_db_conn()
   curs   = conn.cursor()
   
   try:
      curs.execute("ALTER TABLE base_contactrole ALTER COLUMN resource_id DROP NOT NULL")
      curs.execute("ALTER TABLE base_link ALTER COLUMN resource_id DROP NOT NULL")
   except Exception, err:
      try:
         conn.rollback()
      except:
         pass

      traceback.print_exc()

   conn.commit()


def cleanup_db():
   """Remove spurious records from GeoNode DB"""
   conn   = get_db_conn()
   curs   = conn.cursor()

   try:
      curs.execute("DELETE FROM base_contactrole WHERE resource_id is NULL;")
      curs.execute("DELETE FROM base_link WHERE resource_id is NULL;")
   except Exception, err:
      try:
         conn.rollback()
      except:
         pass

      traceback.print_exc()

   conn.commit()


def load_fixture(apps, fixture_file, mangler=None, basepk=-1, owner="admin", datastore='', siteurl=''):

    fixture = open(fixture_file, 'rb')
    
    if mangler:
       objects = json.load(fixture, cls=mangler, **{"basepk":basepk, "owner":owner, "datastore":datastore, "siteurl":siteurl})
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
   with closing(ZipFile(archivename, "w", ZIP_DEFLATED)) as z:
      for root, dirs, files in os.walk(basedir):
         #NOTE: ignore empty directories
         for fn in files:
            absfn = os.path.join(root, fn)
            zfn = absfn[len(basedir)+len(os.sep):] #XXX: relative path
            z.write(absfn, zfn)


def copy_tree(src, dst, symlinks=False, ignore=None):
   for item in os.listdir(src):
       s = os.path.join(src, item)
       d = os.path.join(dst, item)
       if os.path.isdir(s):
           shutil.copytree(s, d, symlinks, ignore)
       else:
           shutil.copy2(s, d)


def unzip_file(zip_file, dst):
   target_folder = os.path.join(dst, os.path.splitext(os.path.basename(zip_file))[0])
   if not os.path.exists(target_folder):
      os.makedirs(target_folder)

   with ZipFile(zip_file, "r") as z:
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



