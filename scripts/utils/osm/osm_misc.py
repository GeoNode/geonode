#!/usr/bin/env python
from geonode.settings import GEONODE_APPS
import geonode.settings as settings
import os
from pprint import pprint
from django.db.models import Q

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")

from geonode.security.models import PermissionLevelMixin
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm, get_anonymous_user

from geonode.layers.models import Layer
osm_layers = Layer.objects.filter(Q(workspace='osm')&Q())
cnt = 1
total = len(osm_layers)
for layer in osm_layers:
    print '#' * 40
    print '%s/%s Layer Name: %s' % (cnt, total, layer.name)
    layer.abstract = '''This layer is acquired from OpenStreetMap (OSM) and is not a product of the DREAM/PHIL-LiDAR 1 Program.

LiPAD uses basemaps from OSM.

(c) OpenStreetMap contributors

https://www.openstreetmap.org/copyright'''
    # pprint('{0} {1}'.format(ctr,layer.name))
    # layer.remove_all_permissions()
    anon_group = Group.objects.get(name='anonymous')
    assign_perm('view_resourcebase', anon_group, layer.get_self_resource())
    assign_perm('download_resourcebase', anon_group,
                layer.get_self_resource())
    assign_perm('view_resourcebase', get_anonymous_user(),
                layer.get_self_resource())
    assign_perm('download_resourcebase', get_anonymous_user(),
                layer.get_self_resource())
    layer.save()
    cnt += 1
    print 'OK'

# osm script for abstract and permission
