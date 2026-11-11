#########################################################################
#
# Copyright (C) 2026 OSGeo
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

from geonode.sources import utils
from geonode.sources.models import DataItem


class DataItemFilterSet(filters.FilterSet):
    # a callable: the provider registry is read per request, not at import
    connection = filters.ModelChoiceFilter(
        field_name="auth_config", queryset=lambda request: utils.source_connections()
    )

    class Meta:
        model = DataItem
        fields = ["connection", "source_provider"]
