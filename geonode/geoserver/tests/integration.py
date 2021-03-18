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
# along with this profgram. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from geonode.tests.base import GeoNodeLiveTestSupport

import timeout_decorator

import os
import time
import gisdata
import logging
from lxml import etree
from defusedxml import lxml as dlxml
from urllib.request import urlopen, Request
from urllib.parse import urljoin

from django.conf import settings
from django.test.utils import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from geonode import geoserver
from geonode.layers.models import Layer
from geonode.compat import ensure_string
from geonode.tests.utils import check_layer
from geonode.layers.utils import file_upload
from geonode.decorators import on_ogc_backend
from geonode.base.models import TopicCategory, Link
from geonode.geoserver.helpers import set_attributes_from_geoserver

LOCAL_TIMEOUT = 300

LOGIN_URL = "/accounts/login/"

logger = logging.getLogger(__name__)


def _log(msg, *args):
    logger.debug(msg, *args)


@override_settings(SITEURL='http://localhost:8001/')
class GeoNodeGeoServerSync(GeoNodeLiveTestSupport):

    """
    Tests GeoNode/GeoServer syncronization
    """
    port = 8001

    def setUp(self):
        super(GeoNodeLiveTestSupport, self).setUp()
        settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED'] = True

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_set_attributes_from_geoserver(self):
        """Test attributes syncronization
        """

        # upload a shapefile
        shp_file = os.path.join(
            gisdata.VECTOR_DATA,
            'san_andres_y_providencia_poi.shp')
        layer = file_upload(shp_file)
        try:
            # set attributes for resource
            for attribute in layer.attribute_set.all():
                attribute.attribute_label = f'{attribute.attribute}_label'
                attribute.description = f'{attribute.attribute}_description'
                attribute.save()

            # sync the attributes with GeoServer
            set_attributes_from_geoserver(layer)

            # tests if everything is synced properly
            for attribute in layer.attribute_set.all():
                self.assertEqual(
                    attribute.attribute_label,
                    f'{attribute.attribute}_label'
                )
                self.assertEqual(
                    attribute.description,
                    f'{attribute.attribute}_description'
                )

            links = Link.objects.filter(resource=layer.resourcebase_ptr)
            self.assertIsNotNone(links)
            self.assertTrue(len(links) > 7)

            original_data_links = [ll for ll in links if 'original' == ll.link_type]
            self.assertEqual(len(original_data_links), 1)

            resp = self.client.get(original_data_links[0].url)
            self.assertEqual(resp.status_code, 200)
        finally:
            # Clean up and completely delete the layers
            layer.delete()


@override_settings(SITEURL='http://localhost:8002/')
class GeoNodeGeoServerCapabilities(GeoNodeLiveTestSupport):

    """
    Tests GeoNode/GeoServer GetCapabilities per layer, user, category and map
    """
    port = 8002

    def setUp(self):
        super(GeoNodeLiveTestSupport, self).setUp()
        settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED'] = True

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_capabilities(self):
        """Test capabilities
        """

        # a category
        category = TopicCategory.objects.all()[0]

        # some users
        norman = get_user_model().objects.get(username="norman")
        admin = get_user_model().objects.get(username="admin")

        # create 3 layers, 2 with norman as an owner an 2 with category as a category
        layer1 = file_upload(
            os.path.join(
                gisdata.VECTOR_DATA,
                "san_andres_y_providencia_poi.shp"),
            name='layer1',
            user=norman,
            category=category,
            overwrite=True,
        )
        layer2 = file_upload(
            os.path.join(
                gisdata.VECTOR_DATA,
                "single_point.shp"),
            name='layer2',
            user=norman,
            overwrite=True,
        )
        layer3 = file_upload(
            os.path.join(
                gisdata.VECTOR_DATA,
                "san_andres_y_providencia_administrative.shp"),
            name='layer3',
            user=admin,
            category=category,
            overwrite=True,
        )
        try:
            namespaces = {'wms': 'http://www.opengis.net/wms',
                          'xlink': 'http://www.w3.org/1999/xlink',
                          'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

            # 0. test capabilities_layer
            url = reverse('capabilities_layer', args=[layer1.id])
            resp = self.client.get(url)
            layercap = dlxml.fromstring(resp.content)
            rootdoc = etree.ElementTree(layercap)
            layernodes = rootdoc.findall('./[wms:Name]', namespaces)
            layernode = layernodes[0]

            self.assertEqual(1, len(layernodes))
            self.assertEqual(layernode.find('wms:Name', namespaces).text,
                             layer1.name)

            # 1. test capabilities_user
            url = reverse('capabilities_user', args=[norman.username])
            resp = self.client.get(url)
            layercap = dlxml.fromstring(resp.content)
            rootdoc = etree.ElementTree(layercap)
            layernodes = rootdoc.findall('./[wms:Name]', namespaces)

            # norman has 2 layers
            self.assertEqual(1, len(layernodes))

            # the norman two layers are named layer1 and layer2
            count = 0
            for layernode in layernodes:
                if layernode.find('wms:Name', namespaces).text == layer1.name:
                    count += 1
                elif layernode.find('wms:Name', namespaces).text == layer2.name:
                    count += 1
            self.assertEqual(1, count)

            # 2. test capabilities_category
            url = reverse('capabilities_category', args=[category.identifier])
            resp = self.client.get(url)
            layercap = dlxml.fromstring(resp.content)
            rootdoc = etree.ElementTree(layercap)
            layernodes = rootdoc.findall('./[wms:Name]', namespaces)

            # category is in two layers
            self.assertEqual(1, len(layernodes))

            # the layers for category are named layer1 and layer3
            count = 0
            for layernode in layernodes:
                if layernode.find('wms:Name', namespaces).text == layer1.name:
                    count += 1
                elif layernode.find('wms:Name', namespaces).text == layer3.name:
                    count += 1
            self.assertEqual(1, count)

            # 3. test for a map
            # TODO
        finally:
            # Clean up and completely delete the layers
            layer1.delete()
            layer2.delete()
            layer3.delete()


@override_settings(SITEURL='http://localhost:8003/')
class GeoNodePermissionsTest(GeoNodeLiveTestSupport):
    """
    Tests GeoNode permissions and its integration with GeoServer
    """
    port = 8003

    def setUp(self):
        super(GeoNodeLiveTestSupport, self).setUp()
        settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED'] = True

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_unpublished(self):
        """Test permissions on an unpublished layer
        """
        thefile = os.path.join(
            gisdata.VECTOR_DATA,
            'san_andres_y_providencia_highway.shp')
        layer = file_upload(thefile, overwrite=True)
        layer.set_default_permissions()
        check_layer(layer)

        # we need some time to have the service up and running
        time.sleep(20)

        try:
            # request getCapabilities: layer must be there as it is published and
            # advertised: we need to check if in response there is
            # <Name>geonode:san_andres_y_providencia_water</Name>
            geoserver_base_url = settings.OGC_SERVER['default']['LOCATION']
            get_capabilities_url = 'ows?' \
                'service=wms&version=1.3.0&request=GetCapabilities'
            url = urljoin(geoserver_base_url, get_capabilities_url)
            str_to_check = '<Name>geonode:san_andres_y_providencia_highway</Name>'
            request = Request(url)
            response = urlopen(request)

            # by default the uploaded layer is published
            self.assertTrue(layer.is_published, True)
            self.assertTrue(any(str_to_check in ensure_string(s) for s in response.readlines()))
        finally:
            # Clean up and completely delete the layer
            layer.delete()

        # with settings disabled
        with self.settings(RESOURCE_PUBLISHING=True):
            layer = file_upload(thefile,
                                overwrite=True,
                                is_approved=False,
                                is_published=False)
            layer.set_default_permissions()
            check_layer(layer)

            # we need some time to have the service up and running
            time.sleep(20)

            try:
                # by default the uploaded layer must be unpublished
                self.assertEqual(layer.is_published, False)

                # check the layer is not in GetCapabilities
                request = Request(url)
                response = urlopen(request)

                # now test with published layer
                layer = Layer.objects.get(pk=layer.pk)
                layer.is_published = True
                layer.save()

                # we need some time to have the service up and running
                time.sleep(20)

                request = Request(url)
                response = urlopen(request)
                self.assertTrue(any(str_to_check in ensure_string(s) for s in response.readlines()))
            finally:
                # Clean up and completely delete the layer
                layer.delete()

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_default_anonymous_permissions(self):
        with override_settings(RESOURCE_PUBLISHING=False,
                               ADMIN_MODERATE_UPLOADS=False,
                               DEFAULT_ANONYMOUS_VIEW_PERMISSION=True,
                               DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION=False):
            self.client.login(username='norman', password='norman')
            norman = get_user_model().objects.get(username="norman")
            saved_layer = file_upload(
                os.path.join(
                    gisdata.VECTOR_DATA,
                    "san_andres_y_providencia_poi.shp"),
                name="san_andres_y_providencia_poi_by_norman",
                user=norman,
                overwrite=True,
            )
            try:
                namespaces = {'wms': 'http://www.opengis.net/wms',
                              'xlink': 'http://www.w3.org/1999/xlink',
                              'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
                url = urljoin(settings.SITEURL, reverse('capabilities_layer', args=[saved_layer.id]))
                resp = self.client.get(url)
                content = resp.content
                self.assertTrue(content)
                layercap = dlxml.fromstring(content)
                rootdoc = etree.ElementTree(layercap)
                layernodes = rootdoc.findall('./[wms:Name]', namespaces)
                layernode = layernodes[0]
                self.assertEqual(1, len(layernodes))
                self.assertEqual(layernode.find('wms:Name', namespaces).text,
                                 saved_layer.name)
                self.client.logout()
                resp = self.client.get(url)
                layercap = dlxml.fromstring(resp.content)
                self.assertIsNotNone(layercap)
            finally:
                # Cleanup
                saved_layer.delete()
