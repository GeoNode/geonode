from datetime import datetime
from datetime import timedelta
from django.core.serializers import serialize
from django.contrib.auth.models import User
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.people.models import Contact
from itertools import cycle
from uuid import uuid4
import os.path


# This is used to populate the database with the search fixture data. This is
# primarly used as a first step to generate the json data for the fixture using
# django's dumpdata


map_data = [
        ('lorem ipsum', 'common lorem ipsum'),
        ('ipsum lorem', 'common ipsum lorem'),
        ('lorem1 ipsum1', 'common abstract1'),
        ('ipsum foo', 'common bar lorem'),
        ('map one', 'common this is a unique thing'),
        ('quux', 'common double thing'),
        ('morx', 'common thing double'),
        ('titledupe something else ', 'whatever common'),
        ('something titledupe else ', 'bar common'),
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
        ('layer1', 'abstract1', 'layer1', 'geonode:layer1', [-180, 180, -90, 90], '19850101'),
        ('layer2', 'abstract2', 'layer2', 'geonode:layer2', [-180, 180, -90, 90], '19800501'),
        ('uniquetitle', 'something here', 'mylayer', 'geonode:mylayer', [-180, 180, -90, 90], '19901001'),
        ('common blar', 'lorem ipsum', 'foo', 'geonode:foo', [-180, 180, -90, 90], '19000603'),
        ('common double it', 'whatever', 'whatever', 'geonode:whatever', [0, 1, 0, 1], '50001101'),
        ('common double time', 'else', 'fooey', 'geonode:fooey', [0, 5, 0, 5], '00010101'),
        ('common bar', 'uniqueabstract', 'quux', 'geonode:quux', [0, 10, 0, 10], '19501209'),
        ('common morx', 'lorem ipsum', 'fleem', 'geonode:fleem', [0, 50, 0, 50], '19630829'),
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
        contact = Contact.objects.get(user=u)
        contact.profile = profile
        contact.save()
        users.append(u)

    for md, user in zip(map_data, cycle(users)):
        title, abstract = md
        m = Map(title=title,
                abstract=abstract,
                zoom=4,
                projection='EPSG:4326',
                center_x=42,
                center_y=-73,
                owner=user,
                )
        m.save()

    for ld, owner in zip(layer_data, cycle(users)):
        title, abstract, name, typename, (bbox_x0, bbox_x1, bbox_y0, bbox_y1), dt = ld
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
                  )
        l.save()


def dump_models(path=None):
    result = serialize("json", sum([list(x) for x in
                                    [User.objects.all(),
                                     Contact.objects.all(),
                                     Layer.objects.all(),
                                     Map.objects.all(),
                                     ]], []))
    if path is None:
        parent, _ = os.path.split(__file__)
        path = os.path.join(parent, 'fixtures', 'silage_testdata.json')
    with open(path, 'w') as f:
        f.write(result)


if __name__ == '__main__':
    create_models()
    dump_models()
