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

import StringIO

from datetime import datetime
from datetime import timedelta
from django.core.serializers import serialize
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from geonode.layers.models import Layer
from geonode.base.models import TopicCategory
from geonode.maps.models import Map, MapLayer
from geonode.documents.models import Document
from geonode.people.models import Profile
from itertools import cycle
from taggit.models import Tag
from taggit.models import TaggedItem
from uuid import uuid4
import os.path


if 'geonode.geoserver' in settings.INSTALLED_APPS:
    from django.db.models import signals
    from geonode.geoserver.signals import geoserver_pre_save_maplayer
    from geonode.geoserver.signals import geoserver_post_save_map
    from geonode.geoserver.signals import geoserver_pre_save
    from geonode.geoserver.signals import geoserver_post_save
    signals.pre_save.disconnect(geoserver_pre_save_maplayer, sender=MapLayer)
    signals.post_save.disconnect(geoserver_post_save_map, sender=Map)
    signals.pre_save.disconnect(geoserver_pre_save, sender=Layer)
    signals.post_save.disconnect(geoserver_post_save, sender=Layer)

# This is used to populate the database with the search fixture data. This is
# primarily used as a first step to generate the json data for the fixture using
# django's dumpdata

imgfile = StringIO.StringIO('GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00'
                                '\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')
f = SimpleUploadedFile('test_img_file.gif', imgfile.read(), 'image/gif')


def all_public():
    '''ensure all layers, maps and documents are publicly viewable'''
    for l in Layer.objects.all():
        l.set_default_permissions()
    for m in Map.objects.all():
        m.set_default_permissions()
    for d in Document.objects.all():
        d.set_default_permissions()


def create_fixtures():
    biota = TopicCategory.objects.get(identifier='biota')
    location = TopicCategory.objects.get(identifier='location')
    elevation = TopicCategory.objects.get(identifier='elevation')
    world_extent = [-180, 180, -90, 90]

    map_data = [
            ('GeoNode Default Map', 'GeoNode default map abstract', ('populartag',), world_extent, biota),
            ('ipsum lorem', 'common ipsum lorem', ('populartag', 'maptagunique'), world_extent, biota),
            ('lorem1 ipsum1', 'common abstract1', ('populartag',), world_extent, biota),
            ('ipsum foo', 'common bar lorem', ('populartag',), world_extent, location),
            ('map one', 'common this is a unique thing', ('populartag',), [0, 1, 0, 1], location),
            ('quux', 'common double thing', ('populartag',), [0, 5, 0, 5], location),
            ('morx', 'common thing double', ('populartag',), [0, 10, 0, 10], elevation),
            ('titledupe something else ', 'whatever common', ('populartag',), [0, 10, 0, 10], elevation),
            ('something titledupe else ', 'bar common', ('populartag',), [0, 50, 0, 50], elevation),
            ]

    user_data = [
            ('user1', 'pass', 'uniquefirst', 'foo'),
            ('user2', 'pass', 'foo', 'uniquelast'),
            ('unique_username', 'pass', 'foo', 'uniquelast'),
            ('jblaze', 'pass', 'johnny', 'blaze'),
            ('foo', 'pass', 'bar', 'baz'),
            ]

    people_data = [
            ('this contains all my interesting profile information',),
            ('some other information goes here',),
            ]

    layer_data = [('CA', 'abstract1', 'CA', 'geonode:CA', world_extent, '19850101', ('populartag', 'here'), elevation),
            ('layer2', 'abstract2', 'layer2', 'geonode:layer2', world_extent, '19800501', ('populartag',), elevation),
            ('uniquetitle', 'something here', 'mylayer', 'geonode:mylayer', world_extent, '19901001', ('populartag',), elevation),  # flake8: noqa
            ('common blar', 'lorem ipsum', 'foo', 'geonode:foo', world_extent, '19000603', ('populartag', 'layertagunique'), location),  # flake8: noqa
            ('common double it', 'whatever', 'whatever', 'geonode:whatever', [0, 1, 0, 1], '50001101', ('populartag',), location),  # flake8: noqa
            ('common double time', 'else', 'fooey', 'geonode:fooey', [0, 5, 0, 5], '00010101', ('populartag',), location),  # flake8: noqa
            ('common bar', 'uniqueabstract', 'quux', 'geonode:quux', [0, 10, 0, 10], '19501209', ('populartag',), biota),   # flake8: noqa
            ('common morx', 'lorem ipsum', 'fleem', 'geonode:fleem', [0, 50, 0, 50], '19630829', ('populartag',), biota),   # flake8: noqa
            ]

    document_data = [('lorem ipsum', 'common lorem ipsum', ('populartag',), world_extent, biota),
                     ('ipsum lorem', 'common ipsum lorem', ('populartag', 'doctagunique'), world_extent, biota),
                     ('lorem1 ipsum1', 'common abstract1', ('populartag',), world_extent, biota),
                     ('ipsum foo', 'common bar lorem', ('populartag',), world_extent, location),
                     ('doc one', 'common this is a unique thing', ('populartag',), [0, 1, 0, 1], location),
                     ('quux', 'common double thing', ('populartag',), [0, 5, 0, 5], location),
                     ('morx', 'common thing double', ('populartag',), [0, 10, 0, 10], elevation),
                     ('titledupe something else ', 'whatever common', ('populartag',), [0, 10, 0, 10], elevation),
                     ('something titledupe else ', 'bar common', ('populartag',), [0, 50, 0, 50], elevation)]

    return map_data, user_data, people_data, layer_data, document_data


def create_models(type=None):
    from django.contrib.auth.models import Group
    map_data, user_data, people_data, layer_data, document_data = create_fixtures()
    anonymous_group, created = Group.objects.get_or_create(name='anonymous')
    u, _ = get_user_model().objects.get_or_create(username='admin', is_superuser=True, first_name='admin')
    u.set_password('admin')
    u.save()
    users = []

    for ud, pd in zip(user_data, cycle(people_data)):
        user_name, password, first_name, last_name = ud
        u, created = get_user_model().objects.get_or_create(username=user_name)
        if created:
            u.first_name = first_name
            u.last_name = last_name
            u.save()
        u.groups.add(anonymous_group)
        users.append(u)

    get_user_model().objects.get(username='AnonymousUser').groups.add(anonymous_group)

    if not type or type == 'map':
        for md, user in zip(map_data, cycle(users)):
            title, abstract, kws, (bbox_x0, bbox_x1, bbox_y0, bbox_y1), category = md
            m = Map(title=title,
                    abstract=abstract,
                    zoom=4,
                    projection='EPSG:4326',
                    center_x=42,
                    center_y=-73,
                    owner=user,
                    bbox_x0=bbox_x0,
                    bbox_x1=bbox_x1,
                    bbox_y0=bbox_y0,
                    bbox_y1=bbox_y1,
                    category=category,
                    )
            m.save()
            for kw in kws:
                m.keywords.add(kw)
                m.save()

    if not type or type == 'document':
        for dd, user in zip(document_data, cycle(users)):
            title, abstract, kws, (bbox_x0, bbox_x1, bbox_y0, bbox_y1), category = dd
            m = Document(title=title,
                         abstract=abstract,
                         owner=user,
                         bbox_x0=bbox_x0,
                         bbox_x1=bbox_x1,
                         bbox_y0=bbox_y0,
                         bbox_y1=bbox_y1,
                         category=category,
                         doc_file=f)
            m.save()
            for kw in kws:
                m.keywords.add(kw)
                m.save()

    if not type or type == 'layer':
        for ld, owner, storeType in zip(layer_data, cycle(users), cycle(('coverageStore', 'dataStore'))):
            title, abstract, name, typename, (bbox_x0, bbox_x1, bbox_y0, bbox_y1), dt, kws, category = ld
            year, month, day = map(int, (dt[:4], dt[4:6], dt[6:]))
            start = datetime(year, month, day)
            end = start + timedelta(days=365)
            l = Layer(title=title,
                      abstract=abstract,
                      name=name,
                      typename=typename,
                      bbox_x0=bbox_x0,
                      bbox_x1=bbox_x1,
                      bbox_y0=bbox_y0,
                      bbox_y1=bbox_y1,
                      uuid=str(uuid4()),
                      owner=owner,
                      temporal_extent_start=start,
                      temporal_extent_end=end,
                      date=start,
                      storeType=storeType,
                      category=category,
                      )
            l.save()
            for kw in kws:
                l.keywords.add(kw)
                l.save()


def dump_models(path=None):
    result = serialize("json", sum([list(x) for x in
                                    [get_user_model().objects.all(),
                                     Profile.objects.all(),
                                     Layer.objects.all(),
                                     Map.objects.all(),
                                     Document.objects.all(),
                                     Tag.objects.all(),
                                     TaggedItem.objects.all(),
                                     ]], []), indent=2, use_natural_keys=True)
    if path is None:
        parent, _ = os.path.split(__file__)
        path = os.path.join(parent, 'fixtures', 'search_testdata.json')
    with open(path, 'w') as f:
        f.write(result)


if __name__ == '__main__':
    create_models()
    dump_models()
