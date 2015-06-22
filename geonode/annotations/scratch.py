from geonode.annotations.models import Annotation
from geonode.annotations.utils import make_point
from geonode.maps.models import Map

def make_annotations(mapid):
    for x in range(10):
        m = Map.objects.get(id=mapid)
        Annotation(map=m, title='ann %s %s' % (mapid, x), content='content', the_geom=make_point(-100 + (10 *x), 40)).save()

