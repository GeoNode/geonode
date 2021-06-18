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
import importlib
import os
from pathlib import Path
from typing import BinaryIO, List, Union
from django.conf import settings

from django.core.exceptions import SuspiciousFileOperation
from django.utils.deconstruct import deconstructible

from . import settings as sm_settings

from abc import ABCMeta, abstractmethod
from django.core.files.storage import FileSystemStorage


class StorageManagerInterface(metaclass=ABCMeta):

    @abstractmethod
    def delete(self, name):
        pass

    @abstractmethod
    def exists(self, name):
        pass

    @abstractmethod
    def listdir(self, path):
        pass

    @abstractmethod
    def open(self, name, mode='rb'):
        pass

    @abstractmethod
    def path(self, name):
        pass

    @abstractmethod
    def save(self, name, content, max_length=None):
        pass

    @abstractmethod
    def url(self, name):
        pass

    @abstractmethod
    def size(self, name):
        pass

    @abstractmethod
    def generate_filename(self, filename):
        pass


@deconstructible
class StorageManager(StorageManagerInterface):

    def __init__(self):
        self._concrete_storage_manager = self._get_concrete_manager()

    def _get_concrete_manager(self):
        module_name, class_name = sm_settings.STORAGE_MANAGER_CONCRETE_CLASS.rsplit(".", 1)
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        return class_()

    def delete(self, name):
        return self._concrete_storage_manager.delete(name)

    def exists(self, name):
        return self._concrete_storage_manager.exists(name)

    def listdir(self, path):
        return self._concrete_storage_manager.listdir(path)

    def open(self, name, mode='rb'):
        return self._concrete_storage_manager.open(name, mode=mode)

    def path(self, name):
        return self._concrete_storage_manager.path(name)

    def save(self, name, content, max_length=None):
        return self._concrete_storage_manager.save(name, content, max_length=max_length)

    def size(self, name):
        return self._concrete_storage_manager.size(name)

    def url(self, name):
        return self._concrete_storage_manager.url(name)

    def replace(self, _resource, files: Union[list, BinaryIO]):
        updated_files = {}
        if isinstance(files, list):
            updated_files['files'] = self._replace_files_list(_resource.files, files)
        elif len(_resource.files):
            updated_files['files'] = [self._replace_single_file(_resource.files[0], files)]
        return updated_files

    def _replace_files_list(self, old_files: List[str], new_files: List[str]):
        out = []
        for f in new_files:
            with open(f, 'rb+') as open_file:
                out.append(self._replace_single_file(old_files[0], open_file))
        return out

    def _replace_single_file(self, old_file: str, new_file: BinaryIO):
        path = str(os.path.basename(Path(old_file).parent.absolute()))
        old_file_name, _ = os.path.splitext(os.path.basename(old_file))
        _, ext = os.path.splitext(new_file.name)
        try:
            filepath = self.save(f"{path}/{old_file_name}{ext}", new_file)
        except SuspiciousFileOperation:
            '''
            If the previous file was in another localtion (due a different storage)
            We will save the file to the new location
            '''
            filepath = self.save(f"{settings.MEDIA_ROOT}{path}/{old_file_name}{ext}", new_file)
        return self.path(filepath)

    def generate_filename(self, filename):
        return self._concrete_storage_manager.generate_filename(filename)


class DefaultStorageManager(StorageManagerInterface):

    def __init__(self):
        self._fsm = FileSystemStorage()

    def _get_concrete_manager(self):
        return DefaultStorageManager()

    def delete(self, name):
        return self._fsm.delete(name)

    def exists(self, name):
        return self._fsm.exists(name)

    def listdir(self, path):
        return self._fsm.listdir(path)

    def open(self, name, mode='rb'):
        return self._fsm.open(name, mode=mode)

    def path(self, name):
        return self._fsm.path(name)

    def save(self, name, content, max_length=None):
        return self._fsm.save(name, content, max_length=max_length)

    def size(self, name):
        return self._fsm.size(name)

    def url(self, name):
        return self._fsm.url(name)

    def generate_filename(self, filename):
        return self._fsm.generate_filename(filename)


storage_manager = StorageManager()
