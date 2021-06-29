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
from storages.utils import setting
from storages.backends.dropbox import (
    _DEFAULT_MODE,
    _DEFAULT_TIMEOUT,
    DropBoxStorage)

from geonode.storage.manager import StorageManagerInterface


class DropboxStorageManager(StorageManagerInterface):

    def __init__(self):
        location = setting('DROPBOX_ROOT_PATH', '/')
        oauth2_access_token = setting('DROPBOX_OAUTH2_TOKEN')
        timeout = setting('DROPBOX_TIMEOUT', _DEFAULT_TIMEOUT)
        write_mode = setting('DROPBOX_WRITE_MODE', _DEFAULT_MODE)

        self._drx = DropBoxStorage(
            oauth2_access_token=oauth2_access_token,
            root_path=location,
            timeout=timeout,
            write_mode=write_mode)

    def _get_concrete_manager(self):
        return DropboxStorageManager()

    def delete(self, name):
        return self._drx.delete(name)

    def exists(self, name):
        return self._drx.exists(name)

    def listdir(self, path):
        return self._drx.listdir(path)

    def open(self, name, mode='rb'):
        return self._drx.open(name, mode=mode)

    def path(self, name):
        return self._drx._full_path(name)

    def save(self, name, content, max_length=None):
        return self._drx.save(name, content)

    def url(self, name):
        return self._drx.url(name)

    def size(self, name):
        return self._drx.size(name)

    def generate_filename(self, filename):
        return self._drx.generate_filename(filename)
