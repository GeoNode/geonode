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
from django.conf import settings
import importlib
from django.utils.module_loading import import_string
import os
from abc import ABCMeta, abstractmethod


class MapHookInterface(metaclass=ABCMeta):
    
    @abstractmethod
    def perform_update(self, upobj, serializer):
        pass

    @abstractmethod
    def perform_create(self, upobj,  serializer):
        pass


class DefaultMapHook(MapHookInterface):
    def perform_create(self, upobj, serializer):
        return NotImplemented

    def perform_update(self, upobj, serializer):
        return NotImplemented


class MapstoreAdapterHook(MapHookInterface):
    def __init__(self):
        self.adapter = self._load_adapter()
    
    def _load_adapter(self):
        cls = settings.MAPSTORE2_ADAPTER_SERIALIZER.split(".")
        module_name, class_name = (".".join(cls[:-1]), cls[-1])
        i = importlib.import_module(module_name)
        hook = getattr(i, class_name)()
        return hook

    def perform_create(self, upobj, serializer):
        return self.adapter.perform_create(upobj, serializer)

    def perform_update(self, upobj, serializer):
        return self.adapter.perform_update(upobj, serializer)


if hasattr(settings, 'MAPSTORE2_ADAPTER_SERIALIZER'):
    adapter = 'geonode.maps.api.hook.MapstoreAdapterHook'
else:
    adapter = os.getenv("MAP_SERIALISER", "geonode.maps.api.hook.DefaultMapHook")

hookset = import_string(adapter)
