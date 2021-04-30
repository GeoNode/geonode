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

import json

from django.conf import settings

from haystack import indexes

from geonode.groups.models import GroupProfile


class GroupIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(boost=2)
    # https://github.com/toastdriven/django-haystack/issues/569 - Necessary for sorting
    title_sortable = indexes.CharField(indexed=False)
    description = indexes.CharField(model_attr='description', boost=1.5)
    id = indexes.IntegerField(model_attr='id')
    type = indexes.CharField(faceted=True)
    json = indexes.CharField(indexed=False)

    def get_model(self):
        return GroupProfile

    def prepare_title(self, obj):
        return str(obj)

    def prepare_title_sortable(self, obj):
        return str(obj).lower()

    def prepare_type(self, obj):
        return "group"

    def prepare_json(self, obj):
        data = {
            "_type": self.prepare_type(obj),

            "title": obj.title,
            "description": obj.description,
            "keywords": [keyword.name for keyword in obj.keywords.all()] if obj.keywords else [],
            "thumb": f"{settings.STATIC_URL}static/img/contact.png",
            "detail": None,
        }

        return json.dumps(data)
