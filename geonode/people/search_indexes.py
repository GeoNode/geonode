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

from haystack import indexes
from geonode.people.models import Profile


class ProfileIndex(indexes.SearchIndex, indexes.Indexable):
    id = indexes.IntegerField(model_attr='id')
    username = indexes.CharField(model_attr='username', null=True)
    first_name = indexes.CharField(model_attr='first_name', null=True)
    last_name = indexes.CharField(model_attr='last_name', null=True)
    profile = indexes.CharField(model_attr='profile', null=True)
    organization = indexes.CharField(model_attr='organization', null=True)
    position = indexes.CharField(model_attr='position', null=True)
    text = indexes.CharField(document=True, use_template=True)
    type = indexes.CharField(faceted=True)

    def get_model(self):
        return Profile

    def prepare_title(self, obj):
        return str(obj)

    def prepare_title_sort(self, obj):
        return str(obj).lower().lstrip()

    def prepare_type(self, obj):
        return "user"
