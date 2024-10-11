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

from geonode.metadata.manager import metadata_manager
from django.views.decorators.csrf import csrf_exempt
from pathlib import Path
from django.http import HttpResponse, JsonResponse

@csrf_exempt
def get_schema(request):

    schema = metadata_manager.get_schema()
    if schema:
        # response = HttpResponse(final_schema, content_type="application/json")
        response = JsonResponse(schema, safe=False)
        return response

    #else:
    #    return response

