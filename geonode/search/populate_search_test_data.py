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

from datetime import datetime
from datetime import timedelta
from django.core.serializers import serialize
from django.contrib.auth.models import User
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.people.models import Profile 
from itertools import cycle
from taggit.models import Tag
from taggit.models import TaggedItem
from uuid import uuid4
import os.path


# This is used to populate the database with the search fixture data. This is
# primarly used as a first step to generate the json data for the fixture using
# django's dumpdata


map_data = [
        ('lorem ipsum', 'common lorem ipsum', ('populartag',)),
        ('ipsum lorem', 'common ipsum lorem', ('populartag', 'maptagunique')),
        ('lorem1 ipsum1', 'common abstract1', ('populartag',)),
        ('ipsum foo', 'common bar lorem', ('populartag',)),
        ('map one', 'common this is a unique thing', ('populartag',)),
        ('quux', 'common double thing', ('populartag',)),
        ('morx', 'common thing double', ('populartag',)),
        ('titledupe something else ', 'whatever common', ('populartag',)),
        ('something titledupe else ', 'bar common', ('populartag',)),
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
        ('layer1', 'abstract1', 'layer1', 'geonode:layer1', [-180, 180, -90, 90], '19850101', ('populartag','here')),
        ('layer2', 'abstract2', 'layer2', 'geonode:layer2', [-180, 180, -90, 90], '19800501', ('populartag',)),
        ('uniquetitle', 'something here', 'mylayer', 'geonode:mylayer', [-180, 180, -90, 90], '19901001', ('populartag',)),
        ('common blar', 'lorem ipsum', 'foo', 'geonode:foo', [-180, 180, -90, 90], '19000603', ('populartag', 'layertagunique')),
        ('common double it', 'whatever', 'whatever', 'geonode:whatever', [0, 1, 0, 1], '50001101', ('populartag',)),
        ('common double time', 'else', 'fooey', 'geonode:fooey', [0, 5, 0, 5], '00010101', ('populartag',)),
        ('common bar', 'uniqueabstract', 'quux', 'geonode:quux', [0, 10, 0, 10], '19501209', ('populartag',)),
        ('common morx', 'lorem ipsum', 'fleem', 'geonode:fleem', [0, 50, 0, 50], '19630829', ('populartag',)),
        ]


def create_models():
    users = []
    for ud, pd in zip(user_data, cycle(people_data)):
        user_name, password, first_name, last_name = ud
        profile = pd[0]
        u = User.objects.create_user(user_name)
        u.first_name = first_name
        u.last_name = last_name
        u.save()
        contact = Profile.objects.get(user=u)
        contact.profile = profile
        contact.save()
        users.append(u)

    for md, user in zip(map_data, cycle(users)):
        title, abstract, kws = md
        m = Map(title=title,
                abstract=abstract,
                zoom=4,
                projection='EPSG:4326',
                center_x=42,
                center_y=-73,
                owner=user,
                )
        m.save()
        for kw in kws:
            m.keywords.add(kw)
            m.save()

    for ld, owner, storeType in zip(layer_data, cycle(users), cycle(('raster','vector'))):
        title, abstract, name, typename, (bbox_x0, bbox_x1, bbox_y0, bbox_y1), dt, kws = ld
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
                  storeType=storeType
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
