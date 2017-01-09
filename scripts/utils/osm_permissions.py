#!/usr/bin/env python
from geonode.settings import GEONODE_APPS
import geonode.settings as settings
import os
from pprint import pprint

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geonode.settings')

from geonode.layers.models import Layer
from geonode.security.models import PermissionLevelMixin
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm, get_anonymous_user

# get osm layers by filtering osm workspace

osm_layers = Layer.objects.filter(workspace__icontains='osm')
ctr = 1
for layer in osm_layers:
    pprint('{0} {1}'.format(ctr,layer.name))
    # layer.remove_all_permissions()
    anon_group = Group.objects.get(name='anonymous')
    assign_perm('view_resourcebase', anon_group, layer.get_self_resource())
    assign_perm('download_resourcebase', anon_group,
                layer.get_self_resource())
    assign_perm('view_resourcebase', get_anonymous_user(),
                layer.get_self_resource())
    assign_perm('download_resourcebase', get_anonymous_user(),
                layer.get_self_resource())
    print 'OK'
    ctr+=1