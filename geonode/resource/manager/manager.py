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
from abc import ABCMeta, abstractmethod


class ResourceManagerInterface(metaclass=ABCMeta):

    @abstractmethod
    def exists(self, uuid):
        pass

    @abstractmethod
    def search(self, filter):
        pass

    @abstractmethod
    def delete(self, uuid):
        pass

    @abstractmethod
    def create(self, uuid):
        pass
