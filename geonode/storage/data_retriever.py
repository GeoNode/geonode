#########################################################################
#
# Copyright (C) 2022 OSGeo
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

import io
import os
import shutil
import logging
import zipfile
import smart_open
from pathlib import Path
from typing import Mapping
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from geonode.storage.exceptions import DataRetrieverExcepion

logger = logging.getLogger(__name__)


class DataItemRetriever(object):

    def __init__(self, _file):
        self.temporary_folder = None
        self.file_path = None

        self._is_django_form_file = False
        self._django_form_file = None
        self._original_file_uri = None
        self._smart_open_uri = None

        if isinstance(_file, UploadedFile):
            '''
            If the file exists and is reachable we can assume that is not a remote file
            '''
            # File provided by django form
            self._django_form_file = _file
            self._is_django_form_file = True
        elif isinstance(_file, str):
            self._is_django_form_file = False
            self._original_file_uri = _file
            self._smart_open_uri = smart_open.parse_uri(_file)
        else:
            raise ValueError()

    def delete_temporary_file(self):
        if (self.temporary_folder and self.file_path and os.path.exists(self.temporary_folder) and os.path.isfile(self.file_path)):
            # Remove File
            os.remove(self.file_path)
            # Verify and remove temp folder
            folder_is_empty = len(os.listdir(self.temporary_folder)) == 0
            folder_is_not_static_root = settings.MEDIA_ROOT != os.path.dirname(os.path.abspath(self.temporary_folder))
            if folder_is_empty and folder_is_not_static_root:
                shutil.rmtree(self.temporary_folder, ignore_errors=True)

        self.temporary_folder = None
        self.file_path = None

    def get_path(self, allow_transfer=True):
        if not self.file_path:
            if allow_transfer:
                self.transfer_remote_file()
        if not self.file_path and os.path.exists(self._original_file_uri):
            return self._original_file_uri
        return self.file_path

    def transfer_remote_file(self, temporary_folder=None):
        from geonode.utils import mkdtemp

        def file_chunks_iterable(file, chunk_size=None):
            """
            Read the file and yield chunks of ``chunk_size`` bytes (defaults to
            ``DEFAULT_BUFFER_CHUNK_SIZE``).
            """
            chunk_size = chunk_size or settings.DEFAULT_BUFFER_CHUNK_SIZE
            try:
                file.seek(0)
            except (AttributeError, io.UnsupportedOperation):
                pass

            while True:
                data = file.read(chunk_size)
                if not data:
                    break
                yield data

        try:
            self.temporary_folder = temporary_folder or mkdtemp()
            self.file_path = os.path.join(self.temporary_folder, self.name)

            if self._is_django_form_file:
                with open(self.file_path, "wb") as tmp_file:
                    for chunk in self._django_form_file.chunks():
                        tmp_file.write(chunk)
            else:
                with open(self.file_path, "wb") as tmp_file, smart_open.open(uri=self._original_file_uri, mode="rb") as original_file:
                    for chunk in file_chunks_iterable(original_file):
                        tmp_file.write(chunk)
        except Exception as e:
            logger.error(e)
            raise DataRetrieverExcepion(detail=e)
        return self.file_path

    @property
    def size(self):
        if self.file_path:
            return os.path.getsize(self.file_path)
        if self._is_django_form_file:
            return os.path.getsize(self._django_form_file)
        if os.path.exists(self._original_file_uri):
            return os.path.getsize(self._original_file_uri)
        return None

    @property
    def name(self):
        if self.file_path:
            return os.path.basename(self.file_path)
        if self._is_django_form_file:
            return (
                self._django_form_file.name
                if hasattr(self._django_form_file, "name")
                else self._django_form_file
            )
        return os.path.basename(self._smart_open_uri.uri_path)


class DataRetriever(object):

    def __init__(self, files, tranfer_at_creation=False):
        self.temporary_folder = None
        self.file_paths = {}

        self.data_items = {
            name: DataItemRetriever(file) for name, file in files.items() if file
        }
        if tranfer_at_creation:
            self.transfer_remote_files()

    def transfer_remote_files(self):
        from geonode.utils import mkdtemp

        self.temporary_folder = mkdtemp()
        for name, data_item_retriever in self.data_items.items():
            file_path = data_item_retriever.transfer_remote_file(self.temporary_folder)
            self.file_paths[name] = Path(file_path)
        '''
        Is more usefull to have always unzipped file than the zip file
        So in case is a zip_file, we unzip it and than delete it
        '''
        if zipfile.is_zipfile(self.file_paths.get('base_file', 'not_zip')):
            self._unzip(zip_name=self.file_paths.get('base_file'))
        return self.file_paths

    def get_paths(self, allow_transfer=False):
        if not self.file_paths:
            if allow_transfer:
                self.transfer_remote_files()
            else:
                raise DataRetrieverExcepion(detail="You can't retrieve paths without clone file first!")
        return self.file_paths.copy()

    def delete_files(self, force=False):
        _folder_exists = self.temporary_folder and os.path.exists(self.temporary_folder)
        if _folder_exists and settings.MEDIA_ROOT != os.path.dirname(os.path.abspath(self.temporary_folder)):
            shutil.rmtree(self.temporary_folder, ignore_errors=True)
        elif force:
            shutil.rmtree(self.temporary_folder, ignore_errors=True)

        self.temporary_folder = None
        self.file_paths = {}

    def get(self, key, default=None):
        return self.data_items.get(key, default)

    def items(self):
        return self.data_items.items()

    def _unzip(self, zip_name: str) -> Mapping:
        from geonode.utils import get_allowed_extensions

        '''
        Function to unzip the file. If is a shp or a tiff
        is assigned as base_file otherwise will create the expected payloads
        at the end the zip is deleted
        '''
        zip_file = self.file_paths['base_file']
        the_zip = zipfile.ZipFile(zip_file, allowZip64=True)
        the_zip.extractall(self.temporary_folder)
        available_choices = get_allowed_extensions()
        not_main_files = ['xml', 'sld', 'zip']
        base_file_choices = [x for x in available_choices if x not in not_main_files]
        for _file in Path(self.temporary_folder).iterdir():
            if any([_file.name.endswith(_ext) for _ext in base_file_choices]):
                self.file_paths['base_file'] = Path(str(_file))
            elif not zipfile.is_zipfile(str(_file)):
                ext = _file.name.split(".")[-1]
                self.file_paths[f"{ext}_file"] = Path(str(_file))

        # remiving the zip file
        os.remove(zip_name)

        # update the data_items
        self.data_items = {
            name: DataItemRetriever(str(_file)) for name, _file in self.file_paths.items() if _file
        }
