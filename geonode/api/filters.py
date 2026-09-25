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

from django_filters import rest_framework as filters
from geonode.groups.models import GroupCategory, GroupProfile
from django.contrib.auth.models import Group

TEXT_LOOKUPS = (
    "exact",
    "contains",
    "icontains",
    "startswith",
    "istartswith",
    "endswith",
    "iendswith",
    "in",
    "isnull",
)


class GroupCategoryFilter(filters.FilterSet):
    class Meta:
        model = GroupCategory
        fields = {
            "slug": TEXT_LOOKUPS,
            "name": TEXT_LOOKUPS,
        }


class GroupProfileFilter(filters.FilterSet):
    class Meta:
        model = GroupProfile
        fields = {
            "title": TEXT_LOOKUPS,
            "slug": TEXT_LOOKUPS,
            "categories__slug": TEXT_LOOKUPS,
            "categories__name": TEXT_LOOKUPS,
        }


class GroupFilter(filters.FilterSet):
    class Meta:
        model = Group
        fields = {
            "name": TEXT_LOOKUPS,
            "groupprofile__title": TEXT_LOOKUPS,
            "groupprofile__slug": TEXT_LOOKUPS,
        }
