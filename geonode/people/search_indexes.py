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
    # Adding these attributes so that the search page functions with elastic search
    is_active = indexes.BooleanField(model_attr='is_active')
    city = indexes.CharField(model_attr='city', null=True)
    country = indexes.CharField(model_attr='country', null=True)
    profile_detail_url = indexes.CharField(model_attr='get_absolute_url', null=True)
    avatar_100 = indexes.CharField(null=True)
    text = indexes.CharField(document=True, use_template=True)
    type = indexes.CharField(faceted=True)
    keywords = indexes.MultiValueField(
        model_attr="keyword_slug_list",
        null=True,
        faceted=True,
        stored=True)

    def prepare_avatar_100(self, obj):
        avatar = obj.avatar_set.first()
        if avatar:
            return avatar.avatar_url(100)
        return ''

    def get_model(self):
        return Profile

    def prepare_title(self, obj):
        return str(obj)

    def prepare_title_sort(self, obj):
        return str(obj).lower().lstrip()

    def prepare_type(self, obj):
        return "user"
