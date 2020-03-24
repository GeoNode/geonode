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
            return {'__type__': '__polygon__', 'ewkt': obj.ewkt}
        return super().default(obj)


def decode_hook(obj):
    if obj.get('__type__', None) == '__polygon__':
        return Polygon.from_ewkt(obj['ewkt'])
    return obj


def dumps(obj):
    return kombujson.dumps(obj, cls=JSONEncoder)


def loads(strng):
    return kombujson.loads(
        strng,
        _loads=partial(json.loads, object_hook=decode_hook)
    )

