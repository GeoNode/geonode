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

import json
import logging
from uuid import uuid4
from unittest.mock import patch
from defusedxml import lxml as dlxml
from django.test.utils import override_settings

from pinax.ratings.models import OverallRating

from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from geonode.base.populate_test_data import create_single_map
from geonode.maps.forms import MapForm

from geonode.maps.models import Map, MapLayer
from geonode.settings import on_travis
from geonode.maps import MapsAppConfig
from geonode.layers.models import Layer
from geonode.compat import ensure_string
from geonode import geoserver
from geonode.decorators import on_ogc_backend
from geonode.maps.utils import fix_baselayers
from geonode.base.models import License, Region
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.tests.utils import NotificationsTestsHelper
from geonode.utils import default_map_config, check_ogc_backend
from geonode.maps.tests_populate_maplayers import create_maplayers

logger = logging.getLogger(__name__)

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


class MapsTest(GeoNodeBaseTestSupport):

    """Tests geonode.maps app/module
    """

    def setUp(self):
        super().setUp()

        self.user = 'admin'
        self.passwd = 'admin'
        create_maplayers()
        self.not_admin = get_user_model().objects.create(username='r-lukaku', is_active=True)
        self.not_admin.set_password('very-secret')
        self.not_admin.save()

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
    @patch('geonode.thumbs.thumbnails.create_thumbnail')
    def test_map_json(self, thumbnail_mock):
        map_obj = Map.objects.all().first()
        map_id = map_obj.id
        # Test that saving a map when not logged in gives 401
        response = self.client.put(
            reverse(
                'map_json',
                args=(
                    str(map_id),
                )),
            data=self.viewer_config,
            content_type="text/json")
        self.assertEqual(response.status_code, 401)

        self.client.login(username=self.user, password=self.passwd)
        response = self.client.put(
            reverse(
                'map_json',
                args=(
                    str(map_id),
                )),
            data=self.viewer_config_alternative,
            content_type="text/json")
        self.assertEqual(response.status_code, 200)

        map_obj = Map.objects.all().first()
        self.assertEqual(map_obj.title, "Title2")
        self.assertEqual(map_obj.abstract, "Abstract2")
        self.assertEqual(map_obj.layer_set.all().count(), 1)

        for map_layer in map_obj.layers:
            self.assertEqual(
                map_layer.layer_title,
                "base:nic_admin")

    @patch('geonode.thumbs.thumbnails.create_thumbnail')
    def test_map_save(self, thumbnail_mock):
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
        self.assertEqual(response.status_code, 200)
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        map_id = int(json.loads(content)['id'])
        self.client.logout()

        # We have now 10 maps and 8 layers
        self.assertEqual(Map.objects.all().count(), 11)
        map_obj = Map.objects.get(id=map_id)
        self.assertEqual(map_obj.title, "Title")
        self.assertEqual(map_obj.abstract, "Abstract")
        self.assertEqual(map_obj.layer_set.all().count(), 1)
        self.assertEqual(map_obj.keyword_list(), ["keywords", "saving"])
        self.assertNotEqual(map_obj.bbox_polygon, None)

        # Test an invalid map creation request
        self.client.login(username=self.user, password=self.passwd)

        try:
            response = self.client.post(
                new_map,
                data="not a valid viewer config",
                content_type="text/json")
            self.assertEqual(response.status_code, 400)
        except Exception:
            pass

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_map_fetch(self):
        """/maps/[id]/data -> Test fetching a map in JSON"""
        map_obj = Map.objects.all().first()
        map_obj.set_default_permissions()
        response = self.client.get(reverse('map_json', args=(map_obj.id,)))
        self.assertEqual(response.status_code, 200)
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        cfg = json.loads(content)
        self.assertEqual(
            cfg["about"]["abstract"],
            'GeoNode default map abstract')
        self.assertEqual(cfg["about"]["title"], 'GeoNode Default Map')
        self.assertEqual(len(cfg["map"]["layers"]), 5)

    def test_map_to_json(self):
        """ Make some assertions about the data structure produced for serialization
            to a JSON map configuration"""
        map_obj = Map.objects.all().first()
        cfg = map_obj.viewer_json(None)
        self.assertEqual(
            cfg['about']['abstract'],
            'GeoNode default map abstract')
        self.assertEqual(cfg['about']['title'], 'GeoNode Default Map')

        def is_wms_layer(x):
            if 'source' in x:
                return cfg['sources'][x['source']]['ptype'] == 'gxp_wmscsource'
            return False
        layernames = [x['name']
                      for x in cfg['map']['layers'] if is_wms_layer(x)]
        self.assertEqual(layernames, ['geonode:CA', ])

    def test_map_to_wmc(self):
        """ /maps/1/wmc -> Test map WMC export
            Make some assertions about the data structure produced
            for serialization to a Web Map Context Document
        """

        map_obj = Map.objects.all().first()
        map_obj.set_default_permissions()
        response = self.client.get(reverse('map_wmc', args=(map_obj.id,)))
        self.assertEqual(response.status_code, 200)

        # check specific XPaths
        wmc = dlxml.fromstring(response.content)

        ns = '{http://www.opengis.net/context}'
        title = f'{ns}General/{ns}Title'
        abstract = f'{ns}General/{ns}Abstract'

        self.assertIsNotNone(wmc.attrib.get('id'))
        self.assertEqual(wmc.find(title).text, 'GeoNode Default Map')
        self.assertEqual(
            wmc.find(abstract).text,
            'GeoNode default map abstract')

    def test_newmap_to_json(self):
        """ Make some assertions about the data structure produced for serialization
            to a new JSON map configuration"""
        response = self.client.get(reverse('new_map_json'))
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        cfg = json.loads(content)
        self.assertEqual(cfg['defaultSourceType'], "gxp_wmscsource")

    def test_map_details(self):
        """/maps/1 -> Test accessing the map browse view function"""
        map_obj = Map.objects.all().first()
        map_obj.set_default_permissions()
        response = self.client.get(reverse('map_detail', args=(map_obj.id,)))
        self.assertEqual(response.status_code, 200)

    @patch('geonode.thumbs.thumbnails.create_thumbnail')
    def test_describe_map(self, thumbnail_mock):
        map_obj = Map.objects.all().first()
        map_obj.set_default_permissions()
        response = self.client.get(reverse('map_metadata_detail', args=(map_obj.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Approved", count=1, status_code=200, msg_prefix='', html=False)
        self.assertContains(response, "Published", count=1, status_code=200, msg_prefix='', html=False)
        self.assertContains(response, "Featured", count=1, status_code=200, msg_prefix='', html=False)
        self.assertContains(response, "<dt>Group</dt>", count=0, status_code=200, msg_prefix='', html=False)

        # ... now assigning a Group to the map
        group = Group.objects.first()
        map_obj.group = group
        map_obj.save()
        response = self.client.get(reverse('map_metadata_detail', args=(map_obj.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<dt>Group</dt>", count=1, status_code=200, msg_prefix='', html=False)
        map_obj.group = None
        map_obj.save()

    def test_new_map_without_layers(self):
        # TODO: Should this test have asserts in it?
        self.client.get(reverse('new_map'))

    def test_new_map_with_layer(self):
        layer = Layer.objects.all().first()
        self.client.get(f"{reverse('new_map')}?layer={layer.alternate}")

    def test_new_map_with_layer_view(self):
        layer = Layer.objects.all().first()
        # anonymous user
        response = self.client.get(f"{reverse('new_map')}?layer={layer.alternate}&view=True")
        self.assertIn('view_resourcebase', response.context.get('perms_list', []))
        self.assertFalse('change_resourcebase' in response.context.get('perms_list', []))
        # admin
        self.client.login(username=self.user, password=self.passwd)
        response = self.client.get(f"{reverse('new_map')}?layer={layer.alternate}&view=True")
        self.assertIn('publish_resourcebase', response.context.get('perms_list', []))
        # Test with invalid layer name
        response = self.client.get(f"{reverse('new_map')}?layer=invalid_name&view=True")
        self.assertListEqual([], response.context.get('perms_list', []))

    def test_new_map_with_empty_bbox_layer(self):
        layer = Layer.objects.all().first()
        self.client.get(f"{reverse('new_map')}?layer={layer.alternate}")

    def test_add_layer_to_existing_map(self):
        layer = Layer.objects.all().first()
        map_obj = Map.objects.all().first()
        self.client.get(f"{reverse('add_layer')}?layer_name={layer.alternate}&map_id={map_obj.id}")

        map_obj = Map.objects.get(id=map_obj.id)
        for map_layer in map_obj.layers:
            layer_title = map_layer.layer_title
            local_link = map_layer.local_link
            if map_layer.name == layer.alternate:
                self.assertTrue(
                    layer_title in layer.alternate)
                self.assertTrue(
                    map_layer.name in local_link)
            if Layer.objects.filter(alternate=map_layer.name).exists():
                attribute_cfg = Layer.objects.get(alternate=map_layer.name).attribute_config()
                if "getFeatureInfo" in attribute_cfg:
                    self.assertIsNotNone(attribute_cfg["getFeatureInfo"])
                    cfg = map_layer.layer_config()
                    self.assertIsNotNone(cfg["getFeatureInfo"])
                    self.assertEqual(cfg["getFeatureInfo"], attribute_cfg["getFeatureInfo"])

    def test_ajax_map_permissions(self):
        """Verify that the ajax_layer_permissions view is behaving as expected
        """

        # Setup some layer names to work with
        mapid = Map.objects.all().first().pk
        invalid_mapid = "42"

        def url(id):
            return reverse('resource_permissions', args=[id])

        # Test that an invalid layer.alternate is handled for properly
        response = self.client.post(
            url(invalid_mapid),
            data=json.dumps(self.perm_spec),
            content_type="application/json")
        self.assertNotEqual(response.status_code, 200)

        # Test that GET returns permissions
        response = self.client.get(url(mapid))
        assert('permissions' in ensure_string(response.content))

        # Test that a user is required to have permissions

        # First test un-authenticated
        response = self.client.post(
            url(mapid),
            data=json.dumps(self.perm_spec),
            content_type="application/json")
        self.assertEqual(response.status_code, 401)

        # Next Test with a user that does NOT have the proper perms
        logged_in = self.client.login(username='foo', password='pass')
        self.assertEqual(logged_in, True)
        response = self.client.post(
            url(mapid),
            data=json.dumps(self.perm_spec),
            content_type="application/json")
        self.assertEqual(response.status_code, 401)

        # Login as a user with the proper permission and test the endpoint
        logged_in = self.client.login(username='admin', password='admin')
        self.assertEqual(logged_in, True)

        response = self.client.post(
            url(mapid),
            data=json.dumps(self.perm_spec),
            content_type="application/json")

        # Test that the method returns 200
        self.assertEqual(response.status_code, 200)

    def test_that_keyword_multiselect_is_not_disabled_for_admin_users(self):
        """
        Test that only admin users can create/edit keywords
        """
        admin_user = get_user_model().objects.get(username='admin')
        self.client.login(username=self.user, password=self.passwd)
        map_id = Map.objects.all().first().id
        url = reverse('map_metadata', args=(map_id,))

        with self.settings(FREETEXT_KEYWORDS_READONLY=True):
            response = self.client.get(url)
            self.assertTrue(admin_user.is_superuser)
            self.assertFalse(response.context['form']['keywords'].field.disabled)

    def test_that_keyword_multiselect_is_disabled_for_non_admin_users(self):
        """
        Test that keyword multiselect widget is disabled when the user is not an admin
        when FREETEXT_KEYWORDS_READONLY=False
        """
        test_map = Map.objects.create(uuid=str(uuid4()), owner=self.not_admin, title='test', is_approved=True,
                                      zoom=0, center_x=0.0, center_y=0.0)
        self.client.login(username=self.not_admin.username, password='very-secret')
        url = reverse('map_metadata', args=(test_map.pk,))
        with self.settings(FREETEXT_KEYWORDS_READONLY=True):
            response = self.client.get(url)
            self.assertFalse(self.not_admin.is_superuser)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['form']['keywords'].field.disabled)

    def test_that_non_admin_user_cannot_create_edit_keyword(self):
        """
        Test that non admin users cannot edit/create keywords when FREETEXT_KEYWORDS_READONLY=False
        """
        test_map = Map.objects.create(uuid=str(uuid4()), owner=self.not_admin, title='test', is_approved=True,
                                      zoom=0, center_x=0.0, center_y=0.0)
        self.client.login(username=self.not_admin.username, password='very-secret')
        url = reverse('map_metadata', args=(test_map.pk,))

        with self.settings(FREETEXT_KEYWORDS_READONLY=True):
            response = self.client.post(url, data={'resource-keywords': 'wonderful-keyword'})
            self.assertFalse(self.not_admin.is_superuser)
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.content, b'Unauthorized: Cannot edit/create Free-text Keywords')

    def test_that_non_admin_user_can_create_write_to_map_without_keyword(self):
        """
        Test that non admin users can write to maps without creating/editing keywords
        when FREETEXT_KEYWORDS_READONLY=False
        """
        test_map = Map.objects.create(uuid=str(uuid4()), owner=self.not_admin, title='test', is_approved=True,
                                      zoom=0, center_x=0.0, center_y=0.0)
        self.client.login(username=self.not_admin.username, password='very-secret')
        url = reverse('map_metadata', args=(test_map.pk,))

        with self.settings(FREETEXT_KEYWORDS_READONLY=True):
            response = self.client.post(url, data={
                "resource-owner": self.not_admin.id,
                "resource-title": "doc",
                "resource-date": "2022-01-24 16:38 pm",
                "resource-date_type": "creation",
                "resource-language": "eng"
            })
            self.assertFalse(self.not_admin.is_superuser)
            self.assertEqual(response.status_code, 200)
        test_map.refresh_from_db()
        self.assertEqual("doc", test_map.title)

    def test_that_keyword_multiselect_is_enabled_for_non_admin_users_when_freetext_keywords_readonly_istrue(self):
        """
        Test that keyword multiselect widget is not disabled when the user is not an admin
        and FREETEXT_KEYWORDS_READONLY=False
        """
        test_map = Map.objects.create(uuid=str(uuid4()), owner=self.not_admin, title='test', is_approved=True,
                                      zoom=0, center_x=0.0, center_y=0.0)
        self.client.login(username=self.not_admin.username, password='very-secret')
        url = reverse('map_metadata', args=(test_map.pk,))
        with self.settings(FREETEXT_KEYWORDS_READONLY=False):
            response = self.client.get(url)
            self.assertFalse(self.not_admin.is_superuser)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context['form']['keywords'].field.disabled)

    def test_that_non_admin_user_can_create_edit_keyword_when_freetext_keywords_readonly_istrue(self):
        """
        Test that non admin users can edit/create keywords when FREETEXT_KEYWORDS_READONLY=False
        """
        test_map = Map.objects.create(uuid=str(uuid4()), owner=self.not_admin, title='test', is_approved=True,
                                      zoom=0, center_x=0.0, center_y=0.0)
        self.client.login(username=self.not_admin.username, password='very-secret')
        url = reverse('map_metadata', args=(test_map.pk,))

        with self.settings(FREETEXT_KEYWORDS_READONLY=False):
            response = self.client.post(url, data={
                "resource-owner": self.not_admin.id,
                "resource-title": "map",
                "resource-date": "2022-01-24 16:38 pm",
                "resource-date_type": "creation",
                "resource-language": "eng",
                'resource-keywords': 'wonderful-keyword'
            })
            self.assertFalse(self.not_admin.is_superuser)
            self.assertEqual(response.status_code, 200)
        test_map.refresh_from_db()
        self.assertEqual("map", test_map.title)

    @patch('geonode.thumbs.thumbnails.create_thumbnail')
    def test_map_metadata(self, thumbnail_mock):
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
        self.assertEqual(response.status_code, 200)
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        map_id = int(json.loads(content)['id'])
        self.client.logout()

        url = reverse('map_metadata', args=(map_id,))

        # test unauthenticated user to modify map metadata
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        # test a user without metadata modify permission
        self.client.login(username='foo', password='pass')
        response = self.client.post(url)
        self.assertTrue(response.status_code in (401, 403))
        self.client.logout()

        # Now test with a valid user using GET method
        self.client.login(username=self.user, password=self.passwd)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Now test with a valid user using POST method
        user = get_user_model().objects.filter(username='admin').first()
        self.client.login(username=self.user, password=self.passwd)
        response = self.client.post(url, data={
            "resource-owner": user.id,
            "resource-title": "map_title",
            "resource-date": "2022-01-24 16:38 pm",
            "resource-date_type": "creation",
            "resource-language": "eng",
        })
        self.assertEqual(response.status_code, 200)

        # TODO: only invalid mapform is tested

    @override_settings(ASYNC_SIGNALS=False)
    @patch('geonode.thumbs.thumbnails.create_thumbnail')
    def test_map_remove(self, thumbnail_mock):
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
        self.assertEqual(response.status_code, 200)
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        map_id = int(json.loads(content)['id'])
        self.client.logout()

        url = reverse('map_remove', args=(map_id,))

        # test unauthenticated user to remove map
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        # test a user without map removal permission
        self.client.login(username='foo', password='pass')
        response = self.client.post(url)
        self.assertTrue(response.status_code in (401, 403))
        self.client.logout()

        # Now test with a valid user using GET method
        self.client.login(username=self.user, password=self.passwd)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Now test with a valid user using POST method,
        # which removes map and associated layers, and redirects webpage
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/maps/' in response['Location'])

        # After removal, map is not existent
        """
        Deletes a map and the associated map layers.
        """
        try:
            map_obj = Map.objects.get(id=map_id)
            map_obj.layer_set.all().delete()
            map_obj.delete()
        except Map.DoesNotExist:
            pass
        url = reverse('map_detail', args=(map_id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @patch('geonode.thumbs.thumbnails.create_thumbnail')
    def test_map_embed(self, thumbnail_mock):
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
        self.assertEqual(response.status_code, 200)
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        map_id = int(json.loads(content)['id'])
        self.client.logout()

        url = reverse('map_embed', args=(map_id,))
        url_no_id = reverse('map_embed')

        # Now test with a map id
        self.client.login(username=self.user, password=self.passwd)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # The embedded map is exempt from X-FRAME-OPTIONS restrictions.
        if hasattr(response, 'xframe_options_exempt'):
            self.assertTrue(response.xframe_options_exempt)

        # Config equals to that of the map whose id is given
        map_obj = Map.objects.get(id=map_id)
        config_map = map_obj.viewer_json(None)
        response_config_dict = json.loads(response.context['config'])
        self.assertEqual(
            config_map['about']['abstract'],
            response_config_dict['about']['abstract'])
        self.assertEqual(
            config_map['about']['title'],
            response_config_dict['about']['title'])

        # Now test without a map id
        response = self.client.get(url_no_id)
        self.assertEqual(response.status_code, 200)
        # Config equals to that of the default map
        config_default = default_map_config(None)[0]
        response_config_dict = json.loads(response.context['config'])
        self.assertEqual(
            config_default['about']['abstract'],
            response_config_dict['about']['abstract'])
        self.assertEqual(
            config_default['about']['title'],
            response_config_dict['about']['title'])

        map_obj.update_from_viewer(config_map, context={})
        title = config_map.get('title', config_map['about']['title'])
        abstract = config_map.get('abstract', config_map['about']['abstract'])
        center = config_map['map'].get('center', settings.DEFAULT_CONTENT_TYPE)
        zoom = config_map['map'].get('zoom', settings.DEFAULT_MAP_ZOOM)

        projection = config_map['map']['projection']

        self.assertEqual(map_obj.title, title)
        self.assertEqual(map_obj.abstract, abstract)
        self.assertEqual(map_obj.center_x, center['x'] if isinstance(center, dict) else center[0])
        self.assertEqual(map_obj.center_y, center['y'] if isinstance(center, dict) else center[1])
        self.assertEqual(map_obj.zoom, zoom)
        self.assertEqual(map_obj.projection, projection)

    @patch('geonode.thumbs.thumbnails.create_thumbnail')
    def test_map_view(self, thumbnail_mock):
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
        self.assertEqual(response.status_code, 200)
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        map_id = int(json.loads(content)['id'])
        self.client.logout()

        url = reverse('map_view', args=(map_id,))

        # test unauthenticated user to view map
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # TODO: unauthenticated user can still access the map view

        # test a user without map view permission
        self.client.login(username='norman', password='norman')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        # TODO: the user can still access the map view without permission

        # Now test with a valid user using GET method
        self.client.login(username=self.user, password=self.passwd)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Config equals to that of the map whose id is given
        map_obj = Map.objects.get(id=map_id)
        config_map = map_obj.viewer_json(None)
        response_config_dict = json.loads(response.context['config'])
        self.assertEqual(
            config_map['about']['abstract'],
            response_config_dict['about']['abstract'])
        self.assertEqual(
            config_map['about']['title'],
            response_config_dict['about']['title'])

        map_obj.update_from_viewer(config_map, context={})
        title = config_map.get('title', config_map['about']['title'])
        abstract = config_map.get('abstract', config_map['about']['abstract'])
        center = config_map['map'].get('center', settings.DEFAULT_MAP_CENTER)
        zoom = config_map['map'].get('zoom', settings.DEFAULT_MAP_ZOOM)
        projection = config_map['map']['projection']

        self.assertEqual(map_obj.title, title)
        self.assertEqual(map_obj.abstract, abstract)
        self.assertEqual(map_obj.center_x, center['x'] if isinstance(center, dict) else center[0])
        self.assertEqual(map_obj.center_y, center['y'] if isinstance(center, dict) else center[1])
        self.assertEqual(map_obj.zoom, zoom)
        self.assertEqual(map_obj.projection, projection)

        for map_layer in map_obj.layers:
            if Layer.objects.filter(alternate=map_layer.name).exists():
                cfg = map_layer.layer_config()
                self.assertIsNotNone(cfg["getFeatureInfo"])

    @patch('geonode.thumbs.thumbnails.create_thumbnail')
    def test_new_map_config(self, thumbnail_mock):
        """Test that new map config can be properly assigned
        """
        self.client.login(username='admin', password='admin')

        # Test successful new map creation
        m = Map()
        admin_user = get_user_model().objects.get(username='admin')
        layer_name = Layer.objects.all().first().alternate
        m.create_from_layer_list(admin_user, [layer_name], "title", "abstract")
        map_id = m.id

        url = reverse('new_map_json')

        # Test GET method with COPY
        response = self.client.get(url, {'copy': map_id})
        self.assertEqual(response.status_code, 200)
        map_obj = Map.objects.get(id=map_id)
        config_map = map_obj.viewer_json(None)
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        response_config_dict = json.loads(content)
        self.assertEqual(
            config_map['map']['layers'],
            response_config_dict['map']['layers'])

        # Test GET method no COPY and no layer in params
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        config_default = default_map_config(None)[0]
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        response_config_dict = json.loads(content)
        self.assertEqual(
            config_default['about']['abstract'],
            response_config_dict['about']['abstract'])
        self.assertEqual(
            config_default['about']['title'],
            response_config_dict['about']['title'])

        # Test GET method no COPY but with layer in params
        response = self.client.get(url, {'layer': layer_name})
        self.assertEqual(response.status_code, 200)
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        response_dict = json.loads(content)
        self.assertEqual(response_dict['fromLayer'], True)

        # Test POST method without authentication
        self.client.logout()
        response = self.client.post(url, {'layer': layer_name})
        self.assertEqual(response.status_code, 401)

        # Test POST method with authentication and a layer in params
        self.client.login(username='admin', password='admin')

        try:
            response = self.client.post(url, {'layer': layer_name})
            # Should not accept the request
            self.assertEqual(response.status_code, 400)

            # Test POST method with map data in json format
            response = self.client.post(
                url,
                data=self.viewer_config,
                content_type="text/json")
            self.assertEqual(response.status_code, 200)
            content = response.content
            if isinstance(content, bytes):
                content = content.decode('UTF-8')
            map_id = int(json.loads(content)['id'])
            # Check new map saved
            map_obj = Map.objects.get(id=map_id)
            # Check
            # BBox format: [xmin, xmax, ymin, ymax
            bbox_str = [
                '-90.193207913954200', '-79.206792062465500',
                '9.059219904470890', '16.540780092025600', 'EPSG:4326']

            self.assertEqual(
                bbox_str,
                [str(c) for c in map_obj.bbox])
            bbox_long_str = '-90.193207913954200,9.059219904470890,' \
                            '-79.206792062465500,16.540780092025600'
            self.assertEqual(bbox_long_str, map_obj.bbox_string)

            # Test methods other than GET or POST and no layer in params
            response = self.client.put(url)
            self.assertEqual(response.status_code, 405)
        except Exception:
            pass

    @patch('geonode.thumbs.thumbnails.create_thumbnail')
    def test_rating_map_remove(self, thumbnail_mock):
        """Test map rating is removed on map remove
        """
        if not on_travis:
            self.client.login(username=self.user, password=self.passwd)
            new_map = reverse('new_map_json')
            logger.debug("Create the map")
            response = self.client.post(
                new_map,
                data=self.viewer_config,
                content_type="text/json")
            content = response.content
            if isinstance(content, bytes):
                content = content.decode('UTF-8')
            map_id = int(json.loads(content)['id'])
            ctype = ContentType.objects.get(model='map')
            logger.debug("Create the rating with the correct content type")
            try:
                OverallRating.objects.create(
                    category=1,
                    object_id=map_id,
                    content_type=ctype,
                    rating=3)
            except Exception as e:
                logger.exception(e)
            logger.debug("Remove the map")
            try:
                response = self.client.post(reverse('map_remove', args=(map_id,)))
                self.assertEqual(response.status_code, 302)
            except Exception as e:
                logger.exception(e)
            logger.debug("Check there are no ratings matching the removed map")
            try:
                rating = OverallRating.objects.filter(object_id=map_id)
                self.assertEqual(rating.count(), 0)
            except Exception as e:
                logger.exception(e)

    def test_fix_baselayers(self):
        """Test fix_baselayers function, used by the fix_baselayers command
        """
        map_obj = Map.objects.all().first()
        map_id = map_obj.id

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            # number of base layers (we remove the local geoserver entry from the total)
            n_baselayers = len(settings.MAP_BASELAYERS) - 1
            # number of local layers
            n_locallayers = map_obj.layer_set.filter(local=True).count()
            fix_baselayers(map_id)
            self.assertEqual(1, n_baselayers + n_locallayers)

    def test_batch_edit(self):
        Model = Map
        view = 'map_batch_metadata'
        resources = Model.objects.all()[:3]
        ids = ','.join(str(element.pk) for element in resources)
        # test non-admin access
        self.client.login(username="bobby", password="bob")
        response = self.client.get(reverse(view))
        self.assertTrue(response.status_code in (401, 403))
        # test group change
        group = Group.objects.first()
        self.client.login(username='admin', password='admin')
        response = self.client.post(
            reverse(view),
            data={'group': group.pk, 'ids': ids, 'regions': 1},
        )
        self.assertEqual(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEqual(resource.group, group)
        # test owner change
        owner = get_user_model().objects.first()
        response = self.client.post(
            reverse(view),
            data={'owner': owner.pk, 'ids': ids, 'regions': 1},
        )
        self.assertEqual(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEqual(resource.owner, owner)
        # test license change
        license = License.objects.first()
        response = self.client.post(
            reverse(view),
            data={'license': license.pk, "ids": ids, 'regions': 1},
        )
        self.assertEqual(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEqual(resource.license, license)
        # test regions change
        region = Region.objects.first()
        response = self.client.post(
            reverse(view),
            data={'region': region.pk, 'ids': ids, 'regions': 1},
        )
        self.assertEqual(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            if resource.regions.all():
                self.assertTrue(region in resource.regions.all())
        # test language change
        language = 'eng'
        response = self.client.post(
            reverse(view),
            data={'language': language, 'ids': ids, 'regions': 1},
        )
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEqual(resource.language, language)
        # test keywords change
        keywords = 'some,thing,new'
        response = self.client.post(
            reverse(view),
            data={'keywords': keywords, 'ids': ids, 'regions': 1},
        )
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            for word in resource.keywords.all():
                self.assertTrue(word.name in keywords.split(','))

    def test_get_legend(self):
        layer = Layer.objects.all().first()
        map_layer = MapLayer.objects.filter(name=layer.alternate).exclude(layer_params='').first()
        if map_layer and layer.default_style:
            self.assertIsNone(map_layer.get_legend)
        elif map_layer:
            # when there is no style in layer_params
            self.assertIsNone(map_layer.get_legend)


class MapModerationTestCase(GeoNodeBaseTestSupport):

    def setUp(self):
        super().setUp()

        self.user = 'admin'
        self.passwd = 'admin'
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
            self.assertEqual(response.status_code, 200)
            content = response.content
            if isinstance(content, bytes):
                content = content.decode('UTF-8')
            map_id = int(json.loads(content)['id'])
            _l = Map.objects.get(id=map_id)
            self.assertTrue(_l.is_approved)
            self.assertTrue(_l.is_published)

        with self.settings(ADMIN_MODERATE_UPLOADS=True):
            self.client.login(username=self.user, password=self.passwd)
            new_map = reverse('new_map_json')
            response = self.client.post(new_map,
                                        data=VIEWER_CONFIG,
                                        content_type="text/json")
            self.assertEqual(response.status_code, 200)
            content = response.content
            if isinstance(content, bytes):
                content = content.decode('UTF-8')
            map_id = int(json.loads(content)['id'])
            _l = Map.objects.get(id=map_id)
            self.assertFalse(_l.is_approved)
            self.assertFalse(_l.is_published)


class MapsNotificationsTestCase(NotificationsTestsHelper):

    def setUp(self):
        super().setUp()

        self.user = 'admin'
        self.passwd = 'admin'
        self.u = get_user_model().objects.get(username=self.user)
        self.u.email = 'test@email.com'
        self.u.is_active = True
        self.u.save()
        self.setup_notifications_for(MapsAppConfig.NOTIFICATIONS, self.u)
        self.norman = get_user_model().objects.get(username='norman')
        self.norman.email = 'norman@email.com'
        self.norman.is_active = True
        self.norman.save()
        self.setup_notifications_for(MapsAppConfig.NOTIFICATIONS, self.norman)

    def testMapsNotifications(self):
        with self.settings(
                EMAIL_ENABLE=True,
                NOTIFICATION_ENABLED=True,
                NOTIFICATIONS_BACKEND="pinax.notifications.backends.email.EmailBackend",
                PINAX_NOTIFICATIONS_QUEUE_ALL=False):
            self.clear_notifications_queue()
            self.client.login(username='norman', password='norman')
            new_map = reverse('new_map_json')
            response = self.client.post(
                new_map,
                data=VIEWER_CONFIG,
                content_type="text/json")
            self.assertEqual(response.status_code, 200)
            content = response.content
            if isinstance(content, bytes):
                content = content.decode('UTF-8')
            map_id = int(json.loads(content)['id'])
            _l = Map.objects.get(id=map_id)
            self.assertTrue(self.check_notification_out('map_created', self.u))

            self.clear_notifications_queue()
            _l.title = 'test notifications 2'
            _l.save(notify=True)
            self.assertTrue(self.check_notification_out('map_updated', self.u))

            self.clear_notifications_queue()
            from dialogos.models import Comment
            lct = ContentType.objects.get_for_model(_l)
            comment = Comment(author=self.norman,
                              name=self.u.username,
                              content_type=lct,
                              object_id=_l.id,
                              content_object=_l,
                              comment='test comment')
            comment.save()
            self.assertTrue(self.check_notification_out('map_comment', self.u))

            self.clear_notifications_queue()
            if "pinax.ratings" in settings.INSTALLED_APPS:
                self.clear_notifications_queue()
                from pinax.ratings.models import Rating
                rating = Rating(user=self.norman,
                                content_type=lct,
                                object_id=_l.id,
                                content_object=_l,
                                rating=5)
                rating.save()
                self.assertTrue(self.check_notification_out('map_rated', self.u))


class TestMapForm(GeoNodeBaseTestSupport):
    def setUp(self) -> None:
        self.user = get_user_model().objects.get(username='admin')
        self.map = create_single_map("single_map", owner=self.user)
        self.sut = MapForm

    def test_resource_form_is_invalid_extra_metadata_not_json_format(self):
        self.client.login(username="admin", password="admin")
        url = reverse("map_metadata", args=(self.map.id,))
        response = self.client.post(url, data={
            "resource-owner": self.map.owner.id,
            "resource-title": "map_title",
            "resource-date": "2022-01-24 16:38 pm",
            "resource-date_type": "creation",
            "resource-language": "eng",
            "resource-extra_metadata": "not-a-json"
        })
        expected = {"success": False, "errors": ["extra_metadata: The value provided for the Extra metadata field is not a valid JSON"]}
        self.assertDictEqual(expected, response.json())

    @override_settings(EXTRA_METADATA_SCHEMA={"key": "value"})
    def test_resource_form_is_invalid_extra_metadata_not_schema_in_settings(self):
        self.client.login(username="admin", password="admin")
        url = reverse("map_metadata", args=(self.map.id,))
        response = self.client.post(url, data={
            "resource-owner": self.map.owner.id,
            "resource-title": "map_title",
            "resource-date": "2022-01-24 16:38 pm",
            "resource-date_type": "creation",
            "resource-language": "eng",
            "resource-extra_metadata": "[{'key': 'value'}]"
        })
        expected = {"success": False, "errors": ["extra_metadata: EXTRA_METADATA_SCHEMA validation schema is not available for resource map"]}
        self.assertDictEqual(expected, response.json())

    def test_resource_form_is_invalid_extra_metadata_invalids_schema_entry(self):
        self.client.login(username="admin", password="admin")
        url = reverse("map_metadata", args=(self.map.id,))
        response = self.client.post(url, data={
            "resource-owner": self.map.owner.id,
            "resource-title": "map_title",
            "resource-date": "2022-01-24 16:38 pm",
            "resource-date_type": "creation",
            "resource-language": "eng",
            "resource-extra_metadata": '[{"key": "value"},{"id": "int", "filter_header": "object", "field_name": "object", "field_label": "object", "field_value": "object"}]'
        })
        expected = "extra_metadata: Missing keys: \'field_label\', \'field_name\', \'field_value\', \'filter_header\' at index 0 "
        self.assertIn(expected, response.json()['errors'][0])

    def test_resource_form_is_valid_extra_metadata(self):
        form = self.sut(data={
            "owner": self.map.owner.id,
            "title": "map_title",
            "date": "2022-01-24 16:38 pm",
            "date_type": "creation",
            "language": "eng",
            "extra_metadata": '[{"id": 1, "filter_header": "object", "field_name": "object", "field_label": "object", "field_value": "object"}]'
        })
        self.assertTrue(form.is_valid())
