from geonode.settings import GEONODE_APPS
import geonode.settings as settings
import os
from geonode.cephgeo.models import CephDataObject


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")

def del_objs():
    objs = CephDataObject.objects.all()
    bitanagan_tiles = CephDataObject.objects.filter(name__icontains='_PL1RB171')
    print 'TOTAL OF', len(bitanagan_tiles), 'tiles'
    for obj in bitanagan_tiles:
        print 'DELETING OBJ ', obj.name
        obj.delete()


if __name__ == '__main__':
    del_objs()
