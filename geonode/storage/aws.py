
from geonode.storage.manager import StorageManagerInterface
from storages.backends.s3boto3 import S3Boto3Storage


class AwsStorageManager(StorageManagerInterface):

    def __init__(self):
        self._aws = S3Boto3Storage()

    def _get_concrete_manager(self):
        return AwsStorageManager()

    def delete(self, name):
        return self._aws.delete(name)

    def exists(self, name):
        return self._aws.exists(name)

    def listdir(self, path):
        return self._drx.listdir(path)

    def open(self, name, mode='rb'):
        return self._aws._open(name, mode=mode)

    def path(self, name):
        return self._aws._full_path(name)

    def save(self, name, content):
        return self._aws._save(name, content)

    def size(self, name):
        return self._aws.size(name)
