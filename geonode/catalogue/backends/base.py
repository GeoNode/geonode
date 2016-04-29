# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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


class BaseCatalogueBackend(object):
    """Catalogue abstract base class"""

    def remove_record(self, uuid):
        """Remove record from the catalogue"""
        raise NotImplementedError()

    def create_record(self, item):
        """Create record in the catalogue"""
        raise NotImplementedError()

    def get_record(self, uuid):
        """Get record from the catalogue"""
        raise NotImplementedError()

    def search_records(self, keywords, start, limit, bbox):
        """Search for records from the catalogue"""
        raise NotImplementedError()
