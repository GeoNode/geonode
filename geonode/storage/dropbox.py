# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2021 OSGeo
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
from pathlib import Path
from geonode.storage.manager import StorageManagerInterface
from storages.backends.dropbox import DropBoxStorage


class DropboxStorageManager(StorageManagerInterface):

    def __init__(self):
        self._drx = DropBoxStorage()

    def _get_concrete_manager(self):
        return DropboxStorageManager()

    def delete(self, name):
        return self._drx.delete(name)

    def exists(self, name):
        return self._drx.exists(name)

    def listdir(self, path):
        return self._drx.listdir(path)

    def open(self, name, mode='rb'):
        return self._drx._open(name, mode=mode)

    def path(self, name):
        return self._drx._full_path(name)

    def save(self, name, content, max_length=None):
        return self._drx.save(name, content)

    def url(self, name):
        return self._drx.url(name)

    def size(self, name):
        return self._drx.size(name)

    def replace_files_list(self, old_files: list, new_files: list):
        out = []
        for f in new_files:
            with open(f, 'rb+') as open_file:
                out.append(self.replace_single_file(old_files[0], open_file))
        return out

    def replace_single_file(self, old_file: list, new_file):
        path = str(Path(old_file).parent.absolute())
        old_file_name, _ = os.path.splitext(os.path.basename(old_file))
        _, ext = os.path.splitext(new_file.name)
        filepath = self.save(f"{path}/{old_file_name}{ext}", new_file)
        return self.path(filepath)
