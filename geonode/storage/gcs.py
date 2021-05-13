# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2020 OSGeo
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

from geonode.storage.manager import StorageManagerInterface
from storages.backends.gcloud import GoogleCloudStorage


class GoogleStorageManager(StorageManagerInterface):

    def __init__(self):
        self._drx = GoogleCloudStorage()

    def _get_concrete_manager(self):
        return GoogleStorageManager()

    def delete(self, name):
        return self._drx.delete(name)

    def exists(self, name):
        return self._drx.exists(name)

    def listdir(self, path):
        return self._drx.listdir(path)

    def open(self, name, mode='rb'):
        return self._drx._open(name, mode=mode)

    def path(self, name):
        raise NotImplementedError

    def save(self, name, content):
        return self._drx._save(name, content)

    def size(self, name):
        return self._drx.size(name)
