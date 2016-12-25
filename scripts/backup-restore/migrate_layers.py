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

import traceback
import os, sys
import shutil
import helpers
import json

from django.conf import settings
from django.core.management import call_command
from django.db import (
    DEFAULT_DB_ALIAS, DatabaseError, IntegrityError, connections, router,
    transaction,
)

def migrate_layers(archive, owner):
   """Migrate existing Layers on GeoNode DB"""
   try:
      # Create Target Folder
      restore_folder = 'restore'
      if not os.path.exists(restore_folder):
         os.makedirs(restore_folder)
      
      # Extract ZIP Archive to Target Folder
      target_folder = helpers.unzip_file(archive, restore_folder)

      # Retrieve the max Primary Key from the DB
      from geonode.base.models import ResourceBase
      try:
         higher_pk = ResourceBase.objects.all().order_by("-id")[0].pk
      except:
         higher_pk = 0

      # Restore Fixtures
      for app_name, dump_name in zip(helpers.app_names, helpers.dump_names):
         for mig_name, mangler in zip(helpers.migrations, helpers.manglers):
            if app_name == mig_name:
               fixture_file = os.path.join(target_folder, dump_name+'.json')
         
               print "Deserializing "+fixture_file
               mangler = helpers.load_class(mangler)

               obj = helpers.load_fixture(app_name, fixture_file, mangler=mangler, basepk=higher_pk, owner=owner, datastore=settings.OGC_SERVER['default']['DATASTORE'], siteurl=settings.SITEURL)

               from django.core import serializers

               objects = serializers.deserialize('json', json.dumps(obj), ignorenonexistent=True)
               for obj in objects:
                  obj.save(using=DEFAULT_DB_ALIAS)

   except Exception, err:
      traceback.print_exc()

   print "Restore finished. Please find restored files and dumps into: '"+target_folder+"'."


if __name__ == '__main__':
   os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")

   restore_file = None
   owner        = None
   try:
      restore_file = sys.argv[1]
      owner        = sys.argv[2]
   except:
      pass

   if restore_file and owner:
      if helpers.confirm(prompt='WARNING: The migration may break some of your GeoNode existing Layers. Are you sure you want to proceed?', resp=False):
         migrate_layers(restore_file, owner)
   else:
      print "Please, provide the full path to the ZIP archive to Restore AND the Owner of the imported Layers.\n"
      print "Usage example:  python migrate_layers.py backup/geonode_backup_test.zip admin\n"


