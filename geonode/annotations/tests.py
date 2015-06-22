from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from django.test.client import Client
from geonode.annotations.models import Annotation
from geonode.annotations.utils import make_point
from geonode.annotations.utils import unicode_csv_dict_reader
from geonode.maps.models import Map
import json
import re
import tempfile


@override_settings(DEBUG=True)
class AnnotationsTest(TestCase):
    fixtures = ['initial_data.json', 'map_data.json', 'sample_admin.json']
    c = Client()

    def setUp(self):
        user_model = get_user_model()
        self.bobby, _ = user_model.objects.get_or_create(username='bobby')
        self.admin = user_model.objects.get(username='admin')
        admin_map = Map.objects.create(owner=self.admin, zoom=1, center_x=0, center_y=0, title='map1')
        # have to use a 'dummy' map to create the appropriate JSON
        dummy = Map.objects.get(id=admin_map.id)
        dummy.id += 1
        dummy.save()
        self.dummy = dummy

    def make_annotations(self, mapobj, cnt=100):
        point = make_point(5, 23)
        for a in xrange(cnt):
            # make sure some geometries are missing
            geom = point if cnt % 2 == 0 else None
            # make the names sort nicely by title/number
            Annotation.objects.create(title='ann%2d' % a, map=mapobj, the_geom=geom).save()

    def assertLoginRedirect(self, resp):
        self.assertEqual(302, resp.status_code)
        self.assertTrue(reverse('account_login') in resp['Location'])

    def test_copy_annotations(self):
        self.make_annotations(self.dummy)

        admin_map = Map.objects.create(owner=self.admin, zoom=1, center_x=0, center_y=0, title='map2')
        # have to use a 'dummy' map to create the appropriate JSON
        target = Map.objects.get(id=admin_map.id)
        target.id += 1
        target.save()

        Annotation.objects.copy_map_annotations(self.dummy.id, target)
        # make sure we have 100 and we can resolve the corresponding copies
        self.assertEqual(100, target.annotation_set.count())
        for a in self.dummy.annotation_set.all():
            self.assertTrue(target.annotation_set.get(title=a.title))

    def test_get(self):
        '''make 100 annotations and get them all as well as paging through'''
        self.make_annotations(self.dummy)

        response = self.c.get(reverse('annotations',args=[self.dummy.id]))
        rows = json.loads(response.content)['features']
        self.assertEqual(100, len(rows))

        for p in range(4):
            response = self.c.get(reverse('annotations',args=[self.dummy.id]) + "?page=%s" % p)
            rows = json.loads(response.content)['features']
            self.assertEqual(25, len(rows))
            self.assertEqual('ann%2d' % (25 * p), rows[0]['properties']['title'])

    def test_post(self):
        '''test post operations'''

        # make 1 and update it
        self.make_annotations(self.dummy, 1)
        ann = Annotation.objects.filter(map=self.dummy)[0]
        data = json.dumps({
            'features' : [{
                'geometry' : {'type' : 'Point', 'coordinates' : [ 5.000000, 23.000000 ]},
                "id" : ann.id,
                'properties' : {
                    "title" : "new title",
                    "start_time" : "2001-01-01",
                    "end_time" : 1371136048
                }
            }]
        })
        # without login, expect failure
        resp = self.c.post(reverse('annotations',args=[self.dummy.id]), data, "application/json")
        self.assertLoginRedirect(resp)

        # login and verify change accepted
        self.c.login(username='admin',password='admin')
        resp = self.c.post(reverse('annotations',args=[self.dummy.id]), data, "application/json")
        ann = Annotation.objects.get(id=ann.id)
        self.assertEqual(ann.title, "new title")
        get_x = lambda ann: int(json.loads(ann.the_geom)['coordinates'][0])
        self.assertEqual(get_x(ann), 5)
        self.assertEqual(ann.end_time, 1371136048)
        self.assertEqual(ann.start_time, 978307200)

        # now make a new one with just a title and null stuff
        data = json.dumps({
            'features' : [{
                'properties' : {
                    "title" : "new ann",
                    "geometry" : None
                }
            }]
        })
        resp = self.c.post(reverse('annotations',args=[self.dummy.id]), data, "application/json")
        resp = json.loads(resp.content)
        self.assertEqual(resp['success'], True)
        self.assertEqual([2], resp['ids'])
        ann = Annotation.objects.get(id=ann.id + 1)
        self.assertEqual(ann.title, "new ann")

    def test_delete(self):
        '''test delete operations'''

        # make 10 annotations, drop 4-7
        self.make_annotations(self.dummy, 10)
        data = json.dumps({'action':'delete', 'ids':range(4,8)})
        # verify failure before login
        resp = self.c.post(reverse('annotations',args=[self.dummy.id]), data, "application/json")
        self.assertLoginRedirect(resp)

        # now check success
        self.c.login(username='admin',password='admin')
        resp = self.c.post(reverse('annotations',args=[self.dummy.id]), data, "application/json")
        # these are gone
        ann = Annotation.objects.filter(id__in=range(4,8))
        self.assertEqual(0, ann.count())
        # six remain
        ann = Annotation.objects.filter(map=self.dummy)
        self.assertEqual(6, ann.count())

    def test_csv_upload(self):
        '''test csv upload with update and insert'''

        #@todo cleanup and break out into simpler cases

        self.make_annotations(self.dummy, 2)

        header = u"id,title,content,lat,lon,start_time,end_time,appearance\n"

        # first row is insert, second update (as it has an id)
        fp = tempfile.NamedTemporaryFile(delete=True)
        fp.write((
            header +
            u'"",foo bar,blah,5,10,2001/01/01,2005\n'
            u"1,bar foo,halb,10,20,2010-01-01,,\n"
            u"2,bunk,\u201c,20,30,,,"
        ).encode('utf-8'))
        fp.seek(0)
        # verify failure before login
        resp = self.c.post(reverse('annotations',args=[self.dummy.id]),{'csv':fp})
        self.assertLoginRedirect(resp)
        # still only 2 annotations
        self.assertEqual(2, Annotation.objects.filter(map=self.dummy.id).count())

        # login, rewind the buffer and verify
        self.c.login(username='admin',password='admin')
        fp.seek(0)
        resp = self.c.post(reverse('annotations',args=[self.dummy.id]),{'csv':fp})
        # response type must be text/html for ext fileupload
        self.assertEqual('text/html', resp['content-type'])
        jsresp = json.loads(resp.content)
        self.assertEqual(True, jsresp['success'])
        ann = Annotation.objects.filter(map=self.dummy.id)
        # we uploaded 3, the other 2 should be deleted (overwrite mode)
        self.assertEqual(3, ann.count())
        ann = Annotation.objects.get(title='bar foo')
        get_x = lambda ann: int(json.loads(ann.the_geom)['coordinates'][0])
        self.assertEqual(get_x(ann), 20.)
        ann = Annotation.objects.get(title='bunk')
        self.assertTrue(u'\u201c', ann.content)
        ann = Annotation.objects.get(title='foo bar')
        self.assertEqual('foo bar', ann.title)
        self.assertEqual(get_x(ann), 10.)

        resp = self.c.get(reverse('annotations',args=[self.dummy.id]) + "?csv")
        # the dict reader won't fill out keys for the missing entries
        # verify each row has 7 fields
        for l in resp.content.split('\r\n'):
            if l.strip():
                self.assertEqual(7, len(l.split(',')))
        x = list(unicode_csv_dict_reader(resp.content))
        self.assertEqual(3, len(x))
        by_title = dict( [(v['title'],v) for v in x] )
        # verify round trip of unicode quote
        self.assertEqual(u'\u201c', by_title['bunk']['content'])
        # and times
        self.assertEqual('2010-01-01T00:00:00', by_title['bar foo']['start_time'])
        self.assertEqual('2001-01-01T00:00:00', by_title['foo bar']['start_time'])
        self.assertEqual('2005-01-01T00:00:00', by_title['foo bar']['end_time'])

        # verify windows codepage quotes
        fp = tempfile.NamedTemporaryFile(delete=True)
        fp.write((
            str(header) +
            ',\x93windows quotes\x94,yay,,,,'
        ))
        fp.seek(0)
        resp = self.c.post(reverse('annotations',args=[self.dummy.id]),{'csv':fp})
        ann = Annotation.objects.get(map=self.dummy.id)
        # windows quotes are unicode now
        self.assertEqual(u'\u201cwindows quotes\u201d', ann.title)

        # make sure a bad upload aborts the transaction (and prevents dropping existing)
        fp = tempfile.NamedTemporaryFile(delete=True)
        fp.write((
            str(header) * 2
        ))
        fp.seek(0)
        resp = self.c.post(reverse('annotations',args=[self.dummy.id]),{'csv':fp})
        self.assertEqual(400, resp.status_code)
        # there should only be one that we uploaded before
        Annotation.objects.get(map=self.dummy.id)
        self.assertEqual('yay', ann.content)

        # and check for the errors related to the invalid data we sent
        expected = ['[1] lat : Invalid value for lat : "lat"',
                    '[1] start_time : Unable to read as date : start_time, please format as yyyy-mm-dd',
                    '[1] lon : Invalid value for lon : "lon"',
                    '[1] end_time : Unable to read as date : end_time, please format as yyyy-mm-dd']
        self.assertEqual(expected, re.findall('<li>([^<]*)</li>', resp.content))
