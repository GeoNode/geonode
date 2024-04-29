#########################################################################
#
# Copyright (C) 2024 OSGeo
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
from distutils.util import strtobool
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response


class AdvertisedListMixin(ListModelMixin):
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # advertised
        # if superuser, all resources will be visible, otherwise only the advertised one and
        # the resource which the user is owner will be returned
        user = request.user
        try:
            _filter = request.query_params.get("advertised", "None")
            advertised = strtobool(_filter) if _filter.lower() != "all" else "all"
        except Exception:
            advertised = None

        if advertised == "all":
            pass
        elif advertised is not None:
            queryset = queryset.filter(advertised=advertised)
        else:
            is_admin = user.is_superuser if user and user.is_authenticated else False
            if not is_admin and user and not user.is_anonymous:
                queryset = (queryset.filter(advertised=True) | queryset.filter(owner=user)).distinct()
            elif not user or user.is_anonymous:
                queryset = queryset.filter(advertised=True)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
