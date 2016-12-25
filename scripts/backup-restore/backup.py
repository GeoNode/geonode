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

from django.conf import settings
from django.core.management import call_command

def backup_full():
   """Full Backup of GeoNode DB"""
   try:
      # Create Target Folder
      dir_time_suffix = helpers.get_dir_time_suffix()
      target_folder = os.path.join('backup', dir_time_suffix)
      if not os.path.exists(target_folder):
         os.makedirs(target_folder)

      # Dump Fixtures
      for app_name, dump_name in zip(helpers.app_names, helpers.dump_names):
         print "Dumping '"+app_name+"' into '"+dump_name+".json'."
         output = open(os.path.join(target_folder,dump_name+'.json'),'w') # Point stdout at a file for dumping data to.
         call_command('dumpdata',app_name,format='json',indent=2,natural=True,stdout=output)
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
         static_folder = os.path.join(static_files_folders, os.path.basename(os.path.normpath(static_files_folder)))
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
         template_folder = os.path.join(template_files_folders, os.path.basename(os.path.normpath(template_files_folder)))
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
         locale_folder = os.path.join(locale_files_folders, os.path.basename(os.path.normpath(locale_files_folder)))
         if not os.path.exists(locale_folder):
            os.makedirs(locale_folder)

         helpers.copy_tree(locale_files_folder, locale_folder)
         print "Saved Locale Files from '"+locale_files_folder+"'."

      # Create Final ZIP Archive      
      helpers.zip_dir(target_folder, os.path.join('backup', dir_time_suffix+'.zip'))

      # Cleanup Temp Folder
      shutil.rmtree(target_folder)

      print "Backup Finished. Archive generated '"+os.path.join('backup', dir_time_suffix+'.zip')+"'."

   except Exception, err:
      pass

   traceback.print_exc()


if __name__ == '__main__':
   os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")

   #basedir = sys.argv[1]
   #archivename = sys.argv[2]
   #zipdir(basedir, archivename)
   backup_full()


