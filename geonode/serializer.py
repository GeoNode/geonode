#########################################################################
#
# Copyright (C) 2020 OSGeo
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

from functools import partial
import json

from django.contrib.gis.geos import Polygon
from kombu.utils import json as kombujson


class JSONEncoder(kombujson.JSONEncoder):
    """
    A JSON serializer implementation that supports serialisation
    of `Polygon`s
    """

    def default(self, obj):
        if isinstance(obj, Polygon):
            return {"__type__": "__polygon__", "ewkt": obj.ewkt}
        return super().default(obj)


def decode_hook(obj):
    if obj.get("__type__", None) == "__polygon__":
        return Polygon.from_ewkt(obj["ewkt"])
    return obj


def dumps(obj):
    return kombujson.dumps(obj, cls=JSONEncoder)


def loads(strng):
    return kombujson.loads(strng, _loads=partial(json.loads, object_hook=decode_hook))
