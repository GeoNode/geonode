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

from django.views.generic import View

from geonode.base.enumerations import LINK_TYPES as _LT
from geonode.base.models import Link
from geonode.utils import json_response


LINK_TYPES = [L for L in _LT if L.startswith("OGC:")]


class OWSListView(View):

    def get(self, request):
        out = {'success': True}
        data = []
        out['data'] = data
        for link in Link.objects.filter(link_type__in=LINK_TYPES).distinct('url'):
            data.append({'url': link.url, 'type': link.link_type})
        return json_response(out)


ows_endpoints = OWSListView.as_view()
