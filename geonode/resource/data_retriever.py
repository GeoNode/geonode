import io
import os
import shutil
import smart_open
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile


BUFFER_CHUNK_SIZE = 64 * 1024


def file_chunks_iterable(file, chunk_size=None):
    """
    Read the file and yield chunks of ``chunk_size`` bytes (defaults to
    ``BUFFER_CHUNK_SIZE``).
    """
    chunk_size = chunk_size or BUFFER_CHUNK_SIZE
    try:
        file.seek(0)
    except (AttributeError, io.UnsupportedOperation):
        pass

    while True:
        data = file.read(chunk_size)
        if not data:
            break
        yield data


class DataRetriever(object):
    def __init__(self, file):
        self.temporary_folder = None
        self.file_path = None

        self._is_django_form_file = False
        self._django_form_file = None
        self._original_file_uri = None
        self._smart_open_uri = None

        if isinstance(file, UploadedFile):
            # File provided by django form
            self._django_form_file = file
            self._is_django_form_file = True
        elif isinstance(file, str):
            self._is_django_form_file = False
            self._original_file_uri = file
            self._smart_open_uri = smart_open.parse_uri(file)
        else:
            raise ValueError()

    def delete_temporary_file(self):
        if (self.temporary_folder and
            self.file_path and
            os.path.exists(self.temporary_folder) and
            os.path.isfile(self.file_path)
        ):
            # Remove File
            os.remove(self.file_path)
            # Verify and remove temp folder
            folder_is_empty = len(os.listdir(self.temporary_folder)) == 0
            folder_is_not_static_root = settings.STATIC_ROOT != os.path.dirname(os.path.abspath(self.temporary_folder))
            if folder_is_empty and folder_is_not_static_root:
                os.rmdir(self.temporary_folder)

        self.temporary_folder = None
        self.file_path = None

    def get_path(self, allow_transfer=True):
        if not self.file_path:
            if allow_transfer:
                self.transfer_remote_file()
            else:
                raise ValueError()
        return self.file_path

    def transfer_remote_file(self, temporary_folder=None):
        self.temporary_folder = temporary_folder or tempfile.mkdtemp(dir=settings.STATIC_ROOT)
        self.file_path = os.path.join(self.temporary_folder, self.name)
        if self._is_django_form_file:
            with open(self.file_path, "wb") as tmp_file:
                for chunk in self._django_form_file.chunks():
                    tmp_file.write(chunk)
        else:
            with open(self.file_path, "wb") as tmp_file, smart_open.open(uri=self._original_file_uri, mode="rb") as original_file:
                for chunk in file_chunks_iterable(original_file):
                    tmp_file.write(chunk)
        return self.file_path

    @property
    def size(self):
        return os.path.getsize(self.file_path)

    @property
    def name(self):
        if self.file_path:
            return os.path.basename(self.file_path)

        if self._is_django_form_file:
            return self._django_form_file.name

        return os.path.basename(self._smart_open_uri.uri_path)


class DataRetrieverGroup(object):
    def __init__(self, files, tranfer_at_creation=False):
        self.temporary_folder = None
        self.file_paths = {}

        self.data_retrievers = {
            key: DataRetriever(value) for key, value in files.items() if value
        }
        if tranfer_at_creation:
            self.transfer_remote_files()

    def transfer_remote_files(self):
        self.temporary_folder = tempfile.mkdtemp(dir=settings.STATIC_ROOT)
        for key, value in self.data_retrievers.items():
            file_path = value.transfer_remote_file(self.temporary_folder)
            self.file_paths[key] = file_path

    def get_paths(self, allow_transfer=False):
        if not self.file_paths:
            if allow_transfer:
                self.transfer_remote_files()
            else:
                raise ValueError()
        return self.file_paths.copy()

    def delete_files(self):
        if (self.temporary_folder and
            os.path.exists(self.temporary_folder) and
            settings.STATIC_ROOT != os.path.dirname(os.path.abspath(self.temporary_folder))
        ):
            shutil.rmtree(self.temporary_folder, ignore_errors=True)
        self.temporary_folder = None
        self.file_paths = {}

    def get(self, key, default=None):
        return self.data_retrievers.get(key, default)

    def items(self):
        return self.data_retrievers.items()
