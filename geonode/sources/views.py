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
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from geonode.sources import utils
from geonode.sources.registry import source_provider_registry


def staff_required(view):
    """Same audience as the API: connecting GeoNode to arbitrary databases is an administrative task"""

    @wraps(view)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied()
        return view(request, *args, **kwargs)

    return _wrapped


# the pages are a thin client of the REST API: every read and every change goes through /api/v2/


@staff_required
def connection_list(request):
    return render(request, "sources/connection_list.html")


@staff_required
def connection_create(request, provider_key):
    if not source_provider_registry.get(provider_key):
        raise Http404()
    return render(request, "sources/connection_form.html", {"provider_key": provider_key})


@staff_required
def connection_detail(request, pk):
    get_object_or_404(utils.source_connections(), pk=pk)
    return render(request, "sources/connection_detail.html", {"connection_id": pk})
