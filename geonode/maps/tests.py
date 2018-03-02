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

from datetime import datetime
from lxml import etree

from django.core.urlresolvers import reverse
from django.test import TestCase
try:
    import json
except ImportError:
    from django.utils import simplejson as json
from django.contrib.contenttypes.models import ContentType
from agon_ratings.models import OverallRating
from django.contrib.auth import get_user_model
from django.conf import settings

from geonode.decorators import on_ogc_backend
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.maps.utils import fix_baselayers
from geonode import geoserver, qgis_server
from geonode.utils import default_map_config, check_ogc_backend
from geonode.base.populate_test_data import create_models
from geonode.maps.tests_populate_maplayers import create_maplayers
from geonode.tests.utils import NotificationsTestsHelper
from geonode.maps import MapsAppConfig
from django.contrib.auth.models import Group
from geonode.base.models import License, Region


VIEWER_CONFIG = """
{
  "defaultSourceType": "gx_wmssource",
  "about": {
      "title": "Title",
      "abstract": "Abstract"
  },
  "sources": {
    "capra": {
      "url":"http://localhost:8080/geoserver/wms"
    }
  },
  "map": {
    "projection":"EPSG:3857",
    "units":"m",
    "maxResolution":156543.0339,
    "maxExtent":[-20037508.34,-20037508.34,20037508.34,20037508.34],
    "center":[-9428760.8688778,1436891.8972581],
    "layers":[{
      "source":"capra",
      "buffer":0,
      "wms":"capra",
      "name":"base:nic_admin"
    }],
    "keywords":["saving", "keywords"],
    "zoom":7
  }
}
"""


class MapsTest(TestCase):

    """Tests geonode.maps app/module
    """

    fixtures = ['initial_data.json', 'bobby']

    def setUp(self):
        self.user = 'admin'
        self.passwd = 'admin'
        create_models(type='map')
        create_models(type='layer')
        create_maplayers()

    default_abstract = "This is a demonstration of GeoNode, an application \
for assembling and publishing web based maps.  After adding layers to the map, \
use the Save Map button above to contribute your map to the GeoNode \
community."

    default_title = "GeoNode Default Map"

    # This is a valid map viewer config, based on the sample data provided
    # by andreas in issue 566. -dwins
    viewer_config = VIEWER_CONFIG

    viewer_config_alternative = """
    {
      "defaultSourceType": "gx_wmssource",
      "about": {
          "title": "Title2",
          "abstract": "Abstract2"
      },
      "sources": {
        "capra": {
          "url":"http://localhost:8080/geoserver/wms"
        }
      },
      "map": {
        "projection":"EPSG:3857",
        "units":"m",
        "maxResolution":156543.0339,
        "maxExtent":[-20037508.34,-20037508.34,20037508.34,20037508.34],
        "center":[-9428760.8688778,1436891.8972581],
        "layers":[{
          "source":"capra",
          "buffer":0,
          "wms":"capra",
          "name":"base:nic_admin"
        }],
        "zoom":7
      }
    }
    """

    perm_spec = {
        "users": {
            "admin": [
                "change_resourcebase",
                "change_resourcebase_permissions",
                "view_resourcebase"]},
        "groups": {}}

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_map_json(self):
        # Test that saving a map when not logged in gives 401
        response = self.client.put(
            reverse(
                'map_json',
                args=(
                    '1',
                )),
            data=self.viewer_config,
            content_type="text/json")
        self.assertEqual(response.status_code, 401)

        self.client.login(username=self.user, password=self.passwd)
        response = self.client.put(
            reverse(
                'map_json',
                args=(
                    '1',
                )),
            data=self.viewer_config_alternative,
            content_type="text/json")
        self.assertEqual(response.status_code, 200)

        map_obj = Map.objects.get(id=1)
        self.assertEquals(map_obj.title, "Title2")
        self.assertEquals(map_obj.abstract, "Abstract2")
        self.assertEquals(map_obj.layer_set.all().count(), 1)

    def test_map_save(self):
        """POST /maps/new/data -> Test saving a new map"""

        new_map = reverse("new_map_json")
        # Test that saving a map when not logged in gives 401
        response = self.client.post(
            new_map,
            data=self.viewer_config,
            content_type="text/json")
        self.assertEqual(response.status_code, 401)

        # Test successful new map creation
        self.client.login(username=self.user, password=self.passwd)
        response = self.client.post(
            new_map,
            data=self.viewer_config,
            content_type="text/json")
        self.assertEquals(response.status_code, 200)
        map_id = int(json.loads(response.content)['id'])
        self.client.logout()

        # We have now 9 maps and 8 layers so the next pk will be 18
        self.assertEquals(map_id, 18)
        map_obj = Map.objects.get(id=map_id)
        self.assertEquals(map_obj.title, "Title")
        self.assertEquals(map_obj.abstract, "Abstract")
        self.assertEquals(map_obj.layer_set.all().count(), 1)
        self.assertEquals(map_obj.keyword_list(), [u"keywords", u"saving"])
        self.assertNotEquals(map_obj.bbox_x0, None)

        # Test an invalid map creation request
        self.client.login(username=self.user, password=self.passwd)
        response = self.client.post(
            new_map,
            data="not a valid viewer config",
            content_type="text/json")
        self.assertEquals(response.status_code, 400)
        self.client.logout()

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_map_fetch(self):
        """/maps/[id]/data -> Test fetching a map in JSON"""
        map_obj = Map.objects.get(id=1)
        map_obj.set_default_permissions()
        response = self.client.get(reverse('map_json', args=(map_obj.id,)))
        self.assertEquals(response.status_code, 200)
        cfg = json.loads(response.content)
        self.assertEquals(
            cfg["about"]["abstract"],
            'GeoNode default map abstract')
        self.assertEquals(cfg["about"]["title"], 'GeoNode Default Map')
        self.assertEquals(len(cfg["map"]["layers"]), 5)

    def test_map_to_json(self):
        """ Make some assertions about the data structure produced for serialization
            to a JSON map configuration"""
        map_obj = Map.objects.get(id=1)
        cfg = map_obj.viewer_json(None, None)
        self.assertEquals(
            cfg['about']['abstract'],
            'GeoNode default map abstract')
        self.assertEquals(cfg['about']['title'], 'GeoNode Default Map')

        def is_wms_layer(x):
            if 'source' in x:
                return cfg['sources'][x['source']]['ptype'] == 'gxp_wmscsource'
            return False
        layernames = [x['name']
                      for x in cfg['map']['layers'] if is_wms_layer(x)]
        self.assertEquals(layernames, ['geonode:CA', ])

    def test_map_to_wmc(self):
        """ /maps/1/wmc -> Test map WMC export
            Make some assertions about the data structure produced
            for serialization to a Web Map Context Document
        """

        map_obj = Map.objects.get(id=1)
        map_obj.set_default_permissions()
        response = self.client.get(reverse('map_wmc', args=(map_obj.id,)))
        self.assertEquals(response.status_code, 200)

        # check specific XPaths
        wmc = etree.fromstring(response.content)

        namespace = '{http://www.opengis.net/context}'
        title = '{ns}General/{ns}Title'.format(ns=namespace)
        abstract = '{ns}General/{ns}Abstract'.format(ns=namespace)

        self.assertEquals(wmc.attrib.get('id'), '1')
        self.assertEquals(wmc.find(title).text, 'GeoNode Default Map')
        self.assertEquals(
            wmc.find(abstract).text,
            'GeoNode default map abstract')

    def test_newmap_to_json(self):
        """ Make some assertions about the data structure produced for serialization
            to a new JSON map configuration"""
        response = self.client.get(reverse('new_map_json'))
        cfg = json.loads(response.content)
        self.assertEquals(cfg['defaultSourceType'], "gxp_wmscsource")

    def test_map_details(self):
        """/maps/1 -> Test accessing the map browse view function"""
        map_obj = Map.objects.get(id=1)
        map_obj.set_default_permissions()
        response = self.client.get(reverse('map_detail', args=(map_obj.id,)))
        self.assertEquals(response.status_code, 200)

    def test_describe_map(self):
        map_obj = Map.objects.get(id=1)
        map_obj.set_default_permissions()
        response = self.client.get(reverse('map_metadata_detail', args=(map_obj.id,)))
        self.failUnlessEqual(response.status_code, 200)
        self.assertContains(response, "Approved", count=1, status_code=200, msg_prefix='', html=False)
        self.assertContains(response, "Published", count=1, status_code=200, msg_prefix='', html=False)
        self.assertContains(response, "Featured", count=1, status_code=200, msg_prefix='', html=False)
        self.assertContains(response, "<dt>Group</dt>", count=0, status_code=200, msg_prefix='', html=False)

        # ... now assigning a Group to the map
        group = Group.objects.first()
        map_obj.group = group
        map_obj.save()
        response = self.client.get(reverse('map_metadata_detail', args=(map_obj.id,)))
        self.failUnlessEqual(response.status_code, 200)
        self.assertContains(response, "<dt>Group</dt>", count=1, status_code=200, msg_prefix='', html=False)
        map_obj.group = None
        map_obj.save()

    def test_new_map_without_layers(self):
        # TODO: Should this test have asserts in it?
        self.client.get(reverse('new_map'))

    def test_new_map_with_layer(self):
        layer = Layer.objects.all()[0]
        self.client.get(reverse('new_map') + '?layer=' + layer.alternate)

    def test_new_map_with_empty_bbox_layer(self):
        layer = Layer.objects.all()[0]
        self.client.get(reverse('new_map') + '?layer=' + layer.alternate)

    def test_add_layer_to_existing_map(self):
        layer = Layer.objects.all()[0]
        map_obj = Map.objects.get(id=1)
        self.client.get(reverse('add_layer') + '?layer_name=%s&map_id=%s' % (layer.alternate, map_obj.id))

    def test_ajax_map_permissions(self):
        """Verify that the ajax_layer_permissions view is behaving as expected
        """

        # Setup some layer names to work with
        mapid = Map.objects.all()[0].pk
        invalid_mapid = "42"

        def url(id):
            return reverse('resource_permissions', args=[id])

        # Test that an invalid layer.alternate is handled for properly
        response = self.client.post(
            url(invalid_mapid),
            data=json.dumps(self.perm_spec),
            content_type="application/json")
        self.assertEquals(response.status_code, 404)

        # Test that GET returns permissions
        response = self.client.get(url(mapid))
        assert('permissions' in response.content)

        # Test that a user is required to have permissions

        # First test un-authenticated
        response = self.client.post(
            url(mapid),
            data=json.dumps(self.perm_spec),
            content_type="application/json")
        self.assertEquals(response.status_code, 401)

        # Next Test with a user that does NOT have the proper perms
        logged_in = self.client.login(username='bobby', password='bob')
        self.assertEquals(logged_in, True)
        response = self.client.post(
            url(mapid),
            data=json.dumps(self.perm_spec),
            content_type="application/json")
        self.assertEquals(response.status_code, 401)

        # Login as a user with the proper permission and test the endpoint
        logged_in = self.client.login(username='admin', password='admin')
        self.assertEquals(logged_in, True)

        response = self.client.post(
            url(mapid),
            data=json.dumps(self.perm_spec),
            content_type="application/json")

        # Test that the method returns 200
        self.assertEquals(response.status_code, 200)

        # Test that the permissions specification is applied

    def test_map_metadata(self):
        """Test that map metadata can be properly rendered
        """
        # first create a map

        # Test successful new map creation
        self.client.login(username=self.user, password=self.passwd)
        new_map = reverse('new_map_json')
        response = self.client.post(
            new_map,
            data=self.viewer_config,
            content_type="text/json")
        self.assertEquals(response.status_code, 200)
        map_id = int(json.loads(response.content)['id'])
        self.client.logout()

        url = reverse('map_metadata', args=(map_id,))

        # test unauthenticated user to modify map metadata
        response = self.client.post(url)
        self.assertEquals(response.status_code, 302)

        # test a user without metadata modify permission
        self.client.login(username='norman', password='norman')
        response = self.client.post(url)
        self.assertEquals(response.status_code, 302)
        self.client.logout()

        # Now test with a valid user using GET method
        self.client.login(username=self.user, password=self.passwd)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

        # Now test with a valid user using POST method
        self.client.login(username=self.user, password=self.passwd)
        response = self.client.post(url)
        self.assertEquals(response.status_code, 200)

        # TODO: only invalid mapform is tested

    def test_map_remove(self):
        """Test that map can be properly removed
        """
        # first create a map

        # Test successful new map creation
        self.client.login(username=self.user, password=self.passwd)
        new_map = reverse('new_map_json')
        response = self.client.post(
            new_map,
            data=self.viewer_config,
            content_type="text/json")
        self.assertEquals(response.status_code, 200)
        map_id = int(json.loads(response.content)['id'])
        self.client.logout()

        url = reverse('map_remove', args=(map_id,))

        # test unauthenticated user to remove map
        response = self.client.post(url)
        self.assertEquals(response.status_code, 302)

        # test a user without map removal permission
        self.client.login(username='norman', password='norman')
        response = self.client.post(url)
        self.assertEquals(response.status_code, 302)
        self.client.logout()

        # Now test with a valid user using GET method
        self.client.login(username=self.user, password=self.passwd)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

        # Now test with a valid user using POST method,
        # which removes map and associated layers, and redirects webpage
        response = self.client.post(url)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response['Location'], '/maps/')

        # After removal, map is not existent
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

        # Prepare map object for later test that if it is completely removed
        #   map_obj = Map.objects.get(id=1)

        # TODO: Also associated layers are not existent
        # self.assertEquals(map_obj.layer_set.all().count(), 0)

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_map_download_leaflet(self):
        """ Test that a map can be downloaded as leaflet"""
        # first, get a new map: user needs to login
        self.client.login(username='admin', password='admin')
        new_map = reverse('new_map_json')
        response = self.client.post(
            new_map,
            data=self.viewer_config,
            content_type="text/json")
        self.assertEquals(response.status_code, 200)
        map_id = int(json.loads(response.content)['id'])
        self.client.logout()

        # then, obtain the map using leaflet
        response = self.client.get(
            reverse(
                'map_download_leaflet', args=(map_id, )))

        # download map leafleT should return OK
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.get('Content-Type'), 'html')

    def test_map_embed(self):
        """Test that map can be properly embedded
        """
        # first create a map

        # Test successful new map creation
        self.client.login(username=self.user, password=self.passwd)

        new_map = reverse('new_map_json')
        response = self.client.post(
            new_map,
            data=self.viewer_config,
            content_type="text/json")
        self.assertEquals(response.status_code, 200)
        map_id = int(json.loads(response.content)['id'])
        self.client.logout()

        url = reverse('map_embed', args=(map_id,))
        url_no_id = reverse('map_embed')

        # Now test with a map id
        self.client.login(username=self.user, password=self.passwd)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

        # The embedded map is exempt from X-FRAME-OPTIONS restrictions.
        if hasattr(response, 'xframe_options_exempt'):
            self.assertTrue(response.xframe_options_exempt)

        # Config equals to that of the map whose id is given
        map_obj = Map.objects.get(id=map_id)
        config_map = map_obj.viewer_json(None, None)
        response_config_dict = json.loads(response.context['config'])
        self.assertEquals(
            config_map['about']['abstract'],
            response_config_dict['about']['abstract'])
        self.assertEquals(
            config_map['about']['title'],
            response_config_dict['about']['title'])

        # Now test without a map id
        response = self.client.get(url_no_id)
        self.assertEquals(response.status_code, 200)
        # Config equals to that of the default map
        config_default = default_map_config(None)[0]
        response_config_dict = json.loads(response.context['config'])
        self.assertEquals(
            config_default['about']['abstract'],
            response_config_dict['about']['abstract'])
        self.assertEquals(
            config_default['about']['title'],
            response_config_dict['about']['title'])

    def test_map_view(self):
        """Test that map view can be properly rendered
        """
        # first create a map

        # Test successful new map creation
        self.client.login(username=self.user, password=self.passwd)

        new_map = reverse('new_map_json')
        response = self.client.post(
            new_map,
            data=self.viewer_config,
            content_type="text/json")
        self.assertEquals(response.status_code, 200)
        map_id = int(json.loads(response.content)['id'])
        self.client.logout()

        url = reverse('map_view', args=(map_id,))

        # test unauthenticated user to view map
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        # TODO: unauthenticated user can still access the map view

        # test a user without map view permission
        self.client.login(username='norman', password='norman')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.client.logout()
        # TODO: the user can still access the map view without permission

        # Now test with a valid user using GET method
        self.client.login(username=self.user, password=self.passwd)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

        # Config equals to that of the map whose id is given
        map_obj = Map.objects.get(id=map_id)
        config_map = map_obj.viewer_json(None, None)
        response_config_dict = json.loads(response.context['config'])
        self.assertEquals(
            config_map['about']['abstract'],
            response_config_dict['about']['abstract'])
        self.assertEquals(
            config_map['about']['title'],
            response_config_dict['about']['title'])

    def test_new_map_config(self):
        """Test that new map config can be properly assigned
        """
        self.client.login(username='admin', password='admin')

        # Test successful new map creation
        m = Map()
        admin_user = get_user_model().objects.get(username='admin')
        layer_name = Layer.objects.all()[0].alternate
        m.create_from_layer_list(admin_user, [layer_name], "title", "abstract")
        map_id = m.id

        url = reverse('new_map_json')

        # Test GET method with COPY
        response = self.client.get(url, {'copy': map_id})
        self.assertEquals(response.status_code, 200)
        map_obj = Map.objects.get(id=map_id)
        config_map = map_obj.viewer_json(None, None)
        response_config_dict = json.loads(response.content)
        self.assertEquals(
            config_map['map']['layers'],
            response_config_dict['map']['layers'])

        # Test GET method no COPY and no layer in params
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        config_default = default_map_config(None)[0]
        response_config_dict = json.loads(response.content)
        self.assertEquals(
            config_default['about']['abstract'],
            response_config_dict['about']['abstract'])
        self.assertEquals(
            config_default['about']['title'],
            response_config_dict['about']['title'])

        # Test GET method no COPY but with layer in params
        response = self.client.get(url, {'layer': layer_name})
        self.assertEquals(response.status_code, 200)
        response_dict = json.loads(response.content)
        self.assertEquals(response_dict['fromLayer'], True)

        # Test POST method without authentication
        self.client.logout()
        response = self.client.post(url, {'layer': layer_name})
        self.assertEquals(response.status_code, 401)

        # Test POST method with authentication and a layer in params
        self.client.login(username='admin', password='admin')

        response = self.client.post(url, {'layer': layer_name})
        # Should not accept the request
        self.assertEquals(response.status_code, 400)

        # Test POST method with map data in json format
        response = self.client.post(
            url,
            data=self.viewer_config,
            content_type="text/json")
        self.assertEquals(response.status_code, 200)
        map_id = int(json.loads(response.content)['id'])
        # Check new map saved
        map_obj = Map.objects.get(id=map_id)
        # Check
        # BBox format: [xmin, xmax, ymin, ymax
        bbox_str = [
            '-90.1932079140', '-79.2067920625',
            '9.0592199045', '16.5407800920', 'EPSG:4326']

        self.assertEqual(
            bbox_str,
            [str(c) for c in map_obj.bbox])
        bbox_long_str = '-90.1932079140,9.0592199045,' \
                        '-79.2067920625,16.5407800920'
        self.assertEqual(bbox_long_str, map_obj.bbox_string)

        # Test methods other than GET or POST and no layer in params
        response = self.client.put(url)
        self.assertEquals(response.status_code, 405)

    def test_rating_map_remove(self):
        """Test map rating is removed on map remove
        """
        self.client.login(username=self.user, password=self.passwd)

        new_map = reverse('new_map_json')

        # Create the map
        response = self.client.post(
            new_map,
            data=self.viewer_config,
            content_type="text/json")
        map_id = int(json.loads(response.content)['id'])

        # Create the rating with the correct content type
        ctype = ContentType.objects.get(model='map')
        OverallRating.objects.create(
            category=1,
            object_id=map_id,
            content_type=ctype,
            rating=3)

        # Remove the map
        response = self.client.post(reverse('map_remove', args=(map_id,)))
        self.assertEquals(response.status_code, 302)

        # Check there are no ratings matching the removed map
        rating = OverallRating.objects.filter(category=1, object_id=map_id)
        self.assertEquals(rating.count(), 0)

    def test_fix_baselayers(self):
        """Test fix_baselayers function, used by the fix_baselayers command
        """
        map_id = 1
        map_obj = Map.objects.get(id=map_id)

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            # number of base layers (we remove the local geoserver entry from the total)
            n_baselayers = len(settings.MAP_BASELAYERS) - 1
        elif check_ogc_backend(qgis_server.BACKEND_PACKAGE):
            # QGIS Server backend already excluded local geoserver entry
            n_baselayers = len(settings.MAP_BASELAYERS)

        # number of local layers
        n_locallayers = map_obj.layer_set.filter(local=True).count()

        fix_baselayers(map_id)

        self.assertEquals(map_obj.layer_set.all().count(), n_baselayers + n_locallayers)

    def test_batch_edit(self):
        Model = Map
        view = 'map_batch_metadata'
        resources = Model.objects.all()[:3]
        ids = ','.join([str(element.pk) for element in resources])
        # test non-admin access
        self.client.login(username="bobby", password="bob")
        response = self.client.get(reverse(view, args=(ids,)))
        self.assertEquals(response.status_code, 401)
        # test group change
        group = Group.objects.first()
        self.client.login(username='admin', password='admin')
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'group': group.pk},
        )
        self.assertEquals(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEquals(resource.group, group)
        # test owner change
        owner = get_user_model().objects.first()
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'owner': owner.pk},
        )
        self.assertEquals(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEquals(resource.owner, owner)
        # test license change
        license = License.objects.first()
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'license': license.pk},
        )
        self.assertEquals(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEquals(resource.license, license)
        # test regions change
        region = Region.objects.first()
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'region': region.pk},
        )
        self.assertEquals(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertTrue(region in resource.regions.all())
        # test date change
        date = datetime.now()
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'date': date},
        )
        self.assertEquals(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEquals(resource.date, date)
        # test language change
        language = 'eng'
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'language': language},
        )
        self.assertEquals(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEquals(resource.language, language)
        # test keywords change
        keywords = 'some,thing,new'
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'keywords': keywords},
        )
        self.assertEquals(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            for word in resource.keywords.all():
                self.assertTrue(word.name in keywords.split(','))


class MapModerationTestCase(TestCase):

    fixtures = ['initial_data.json', 'bobby']

    def setUp(self):
        super(MapModerationTestCase, self).setUp()
        self.user = 'admin'
        self.passwd = 'admin'
        create_models(type='layer')
        create_models(type='map')
        self.u = get_user_model().objects.get(username=self.user)
        self.u.email = 'test@email.com'
        self.u.is_active = True
        self.u.save()

    def test_moderated_upload(self):
        """
        Test if moderation flag works
        """
        with self.settings(ADMIN_MODERATE_UPLOADS=False):
            self.client.login(username=self.user, password=self.passwd)
            new_map = reverse('new_map_json')
            response = self.client.post(new_map,
                                        data=VIEWER_CONFIG,
                                        content_type="text/json")
            self.assertEquals(response.status_code, 200)
            map_id = int(json.loads(response.content)['id'])
            l = Map.objects.get(id=map_id)

            self.assertTrue(l.is_published)

        with self.settings(ADMIN_MODERATE_UPLOADS=True):
            self.client.login(username=self.user, password=self.passwd)
            new_map = reverse('new_map_json')
            response = self.client.post(new_map,
                                        data=VIEWER_CONFIG,
                                        content_type="text/json")
            self.assertEquals(response.status_code, 200)
            map_id = int(json.loads(response.content)['id'])
            l = Map.objects.get(id=map_id)

            self.assertFalse(l.is_published)


class MapsNotificationsTestCase(NotificationsTestsHelper):

    fixtures = ['initial_data.json', 'bobby']

    def setUp(self):
        super(MapsNotificationsTestCase, self).setUp()
        self.user = 'admin'
        self.passwd = 'admin'
        create_models(type='layer')
        create_models(type='map')
        self.u = get_user_model().objects.get(username=self.user)
        self.u.email = 'test@email.com'
        self.u.is_active = True
        self.u.save()
        self.setup_notifications_for(MapsAppConfig.NOTIFICATIONS, self.u)

    def testMapsNotifications(self):
        with self.settings(PINAX_NOTIFICATIONS_QUEUE_ALL=True):
            self.clear_notifications_queue()
            self.client.login(username=self.user, password=self.passwd)
            new_map = reverse('new_map_json')
            response = self.client.post(new_map,
                                        data=VIEWER_CONFIG,
                                        content_type="text/json")
            self.assertEquals(response.status_code, 200)
            map_id = int(json.loads(response.content)['id'])
            l = Map.objects.get(id=map_id)
            self.assertTrue(self.check_notification_out('map_created', self.u))
            l.title = 'test notifications 2'
            l.save()
            self.assertTrue(self.check_notification_out('map_updated', self.u))

            from dialogos.models import Comment
            lct = ContentType.objects.get_for_model(l)
            comment = Comment(author=self.u, name=self.u.username,
                              content_type=lct, object_id=l.id,
                              content_object=l, comment='test comment')
            comment.save()

            self.assertTrue(self.check_notification_out('map_comment', self.u))
