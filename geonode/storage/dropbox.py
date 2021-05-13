
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

    def save(self, name, content):
        return self._drx._save(name, content)

    def size(self, name):
        return self._drx.size(name)
