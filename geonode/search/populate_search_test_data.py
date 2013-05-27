#########################################################################
#
# Copyright (C) 2012 OpenPlans
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
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from geonode.layers.models import Layer
from geonode.base.models import TopicCategory
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.people.models import Profile
from itertools import cycle
from taggit.models import Tag
from taggit.models import TaggedItem
from uuid import uuid4
import os.path


# This is used to populate the database with the search fixture data. This is
# primarly used as a first step to generate the json data for the fixture using
# django's dumpdata

imgfile = StringIO.StringIO('GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00'
                                '\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')
f = SimpleUploadedFile('test_img_file.gif', imgfile.read(), 'image/gif')

def create_fixtures():
    biota = TopicCategory.objects.get(slug='biota')
    location = TopicCategory.objects.get(slug='location')
    elevation = TopicCategory.objects.get(slug='elevation')


    map_data = [
            ('GeoNode Default Map', 'GeoNode default map abstract', ('populartag',), [-180, 180, -90, 90], biota),
            ('ipsum lorem', 'common ipsum lorem', ('populartag', 'maptagunique'), [-180, 180, -90, 90], biota),
            ('lorem1 ipsum1', 'common abstract1', ('populartag',), [-180, 180, -90, 90], biota),
            ('ipsum foo', 'common bar lorem', ('populartag',), [-180, 180, -90, 90], location),
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

    layer_data = [
            ('CA', 'abstract1', 'CA', 'base:CA', [-180, 180, -90, 90], '19850101', ('populartag','here'), elevation),
            ('layer2', 'abstract2', 'layer2', 'geonode:layer2', [-180, 180, -90, 90], '19800501', ('populartag',), elevation),
            ('uniquetitle', 'something here', 'mylayer', 'geonode:mylayer', [-180, 180, -90, 90], '19901001', ('populartag',), elevation),
            ('common blar', 'lorem ipsum', 'foo', 'geonode:foo', [-180, 180, -90, 90], '19000603', ('populartag', 'layertagunique'), location),
            ('common double it', 'whatever', 'whatever', 'geonode:whatever', [0, 1, 0, 1], '50001101', ('populartag',), location),
            ('common double time', 'else', 'fooey', 'geonode:fooey', [0, 5, 0, 5], '00010101', ('populartag',), location),
            ('common bar', 'uniqueabstract', 'quux', 'geonode:quux', [0, 10, 0, 10], '19501209', ('populartag',), biota),
            ('common morx', 'lorem ipsum', 'fleem', 'geonode:fleem', [0, 50, 0, 50], '19630829', ('populartag',), biota),
            ]

    document_data = [
            ('lorem ipsum', 'common lorem ipsum', ('populartag',), [-180, 180, -90, 90], biota),
            ('ipsum lorem', 'common ipsum lorem', ('populartag', 'doctagunique'), [-180, 180, -90, 90], biota),
            ('lorem1 ipsum1', 'common abstract1', ('populartag',), [-180, 180, -90, 90], biota),
            ('ipsum foo', 'common bar lorem', ('populartag',), [-180, 180, -90, 90], location),
            ('doc one', 'common this is a unique thing', ('populartag',), [0, 1, 0, 1], location),
            ('quux', 'common double thing', ('populartag',), [0, 5, 0, 5], location),
            ('morx', 'common thing double', ('populartag',), [0, 10, 0, 10], elevation),
            ('titledupe something else ', 'whatever common', ('populartag',), [0, 10, 0, 10], elevation),
            ('something titledupe else ', 'bar common', ('populartag',), [0, 50, 0, 50], elevation),
            ]

    return map_data, user_data, people_data, layer_data, document_data

def create_models(type = None):
    map_data, user_data, people_data, layer_data, document_data = create_fixtures()
    
    u, _ = User.objects.get_or_create(username='admin',is_superuser=True)
    u.set_password('admin')
    u.save()
    users = []


    for ud, pd in zip(user_data, cycle(people_data)):
        user_name, password, first_name, last_name = ud
        profile = pd[0]
        u,created = User.objects.get_or_create(username = user_name)
        if created:
            u.first_name = first_name
            u.last_name = last_name
            u.save()
            contact = Profile.objects.get(user=u)
            contact.profile = profile
            contact.save()
        users.append(u)

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
                    category = category,
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
                    category = category,
                    doc_file = f
                    )
            m.save()
            for kw in kws:
                m.keywords.add(kw)
                m.save()

    if not type or type == 'layer':
        for ld, owner, storeType in zip(layer_data, cycle(users), cycle(('coverageStore','dataStore'))):
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
                      category = category,
                      )
            l.save()
            for kw in kws:
                l.keywords.add(kw)
                l.save()

def dump_models(path=None):
    result = serialize("json", sum([list(x) for x in
                                    [User.objects.all(),
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
