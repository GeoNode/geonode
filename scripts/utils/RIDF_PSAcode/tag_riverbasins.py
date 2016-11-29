#!/usr/bin/env python
from geonode.settings import GEONODE_APPS
import geonode.settings as settings
from geonode.cephgeo.models import RIDF
import os
from pprint import pprint

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")

# get list of RIDF objects
# read rbs_raw, tag as taggable keyword to the RIDF object

def riverbasin_keywords():
    ctr = 0
    ridf_objects = RIDF.objects.all()
    for obj in ridf_objects:
        # multiple riverbasins
        riverbasins = []
        if obj.rbs_raw is not None:
            riverbasins = obj.rbs_raw.split(',')
            ctr+=1

        rb_count = len(riverbasins)
        for ind in range(0, rb_count):
            obj.riverbasins.add(riverbasins[ind].replace('_', ' ').title())
            # pprint('{0} {1}:{2}'.format(ctr, obj.muni_code, riverbasins[ind].replace(
            #     '_', ' ').title()))
        

riverbasin_keywords()

# single riverbasin
