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

from geonode.layers.populate_datasets_data import create_dataset_data
from geonode.geoserver.createlayer.utils import create_dataset
from geonode.tests.base import GeoNodeLiveTestSupport

import timeout_decorator

import time
import logging
from lxml import etree
from owslib.etree import etree as dlxml
from urllib.request import urlopen, Request
from urllib.parse import urljoin

from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test.utils import override_settings

from geonode import geoserver
from geonode.layers.models import Dataset
from geonode.compat import ensure_string
from geonode.tests.utils import check_dataset
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
        layer = Dataset.objects.all().first()
        create_dataset_data(layer.resourcebase_ptr_id)
        try:
            # set attributes for resource
            for attribute in layer.attribute_set.all():
                attribute.attribute_label = f'{attribute.attribute}_label'
                attribute.description = f'{attribute.attribute}_description'
                attribute.save()

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

            # sync the attributes with GeoServer
            # since on geoserver are empty, we expect that now the layer
            # does not have any attribute
            set_attributes_from_geoserver(layer)

            links = Link.objects.filter(resource=layer.resourcebase_ptr)
            self.assertIsNotNone(links)
            self.assertTrue(len(links) >= 7)

            original_data_links = [ll for ll in links if 'original' == ll.link_type]
            self.assertEqual(len(original_data_links), 0)

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
        category = TopicCategory.objects.first()

        # some users
        norman = get_user_model().objects.get(username="norman")
        admin = get_user_model().objects.get(username="admin")

        # create 3 layers, 2 with norman as an owner an 2 with category as a category
        layer1 = create_dataset(
            name='layer1',
            title="san_andres_y_providencia_poi",
            owner_name=norman,
            geometry_type="Point"
        )
        layer2 = create_dataset(
            name='layer2',
            title="single_point",
            owner_name=norman,
            geometry_type="Point"
        )
        layer2.category = category
        layer2.save()
        layer3 = create_dataset(
            name='layer3',
            title="san_andres_y_providencia_administrative",
            owner_name=admin,
            geometry_type="Point"
        )
        layer3.category = category
        layer3.save()
        try:
            namespaces = {'wms': 'http://www.opengis.net/wms',
                          'xlink': 'http://www.w3.org/1999/xlink',
                          'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

            # 0. test capabilities_dataset
            url = reverse('capabilities_dataset', args=[layer1.id])
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
        layer = Dataset.objects.first()
        layer.set_default_permissions()
        check_dataset(layer)

        # we need some time to have the service up and running
        # time.sleep(20)

        try:
            # request getCapabilities: layer must be there as it is published and
            # advertised: we need to check if in response there is
            # <Name>geonode:san_andres_y_providencia_water</Name>
            geoserver_base_url = settings.OGC_SERVER['default']['LOCATION']
            get_capabilities_url = 'ows?' \
                'service=wms&version=1.3.0&request=GetCapabilities'
            url = urljoin(geoserver_base_url, get_capabilities_url)
            str_to_check = f'<Name>geonode:{layer.name}</Name>'
            request = Request(url)
            response = urlopen(request)

            # by default the uploaded layer is published
            self.assertTrue(layer.is_published)
            self.assertTrue(any(str_to_check in ensure_string(s) for s in response.readlines()))
        finally:
            # Clean up and completely delete the layer
            layer.delete()

        # with settings disabled
        with self.settings(RESOURCE_PUBLISHING=True):
            layer = Dataset.objects.first()
            layer.is_approved = False
            layer.is_published = False
            layer.save()
            layer.set_default_permissions()
            check_dataset(layer)

            # we need some time to have the service up and running
            time.sleep(20)

            try:
                # by default the uploaded layer must be unpublished
                self.assertEqual(layer.is_published, False)

                # check the layer is not in GetCapabilities
                request = Request(url)
                response = urlopen(request)

                # now test with published layer
                layer = Dataset.objects.get(pk=layer.pk)
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
        anonymous = get_user_model().objects.get(username="AnonymousUser")
        norman = get_user_model().objects.get(username="norman")
        with override_settings(RESOURCE_PUBLISHING=False,
                               ADMIN_MODERATE_UPLOADS=False,
                               DEFAULT_ANONYMOUS_VIEW_PERMISSION=True,
                               DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION=False):
            self.client.login(username='norman', password='norman')

            saved_dataset = create_dataset(
                name='san_andres_y_providencia_poi_by_norman',
                title='san_andres_y_providencia_poi',
                owner_name=norman,
                geometry_type='Point'
            )

            try:
                namespaces = {'wms': 'http://www.opengis.net/wms',
                              'xlink': 'http://www.w3.org/1999/xlink',
                              'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
                url = urljoin(settings.SITEURL, reverse('capabilities_dataset', args=[saved_dataset.id]))
                resp = self.client.get(url)
                content = resp.content
                self.assertTrue(content)
                layercap = dlxml.fromstring(content)
                rootdoc = etree.ElementTree(layercap)
                layernodes = rootdoc.findall('./[wms:Name]', namespaces)
                layernode = layernodes[0]
                self.assertEqual(1, len(layernodes))
                self.assertEqual(layernode.find('wms:Name', namespaces).text,
                                 saved_dataset.name)
                self.client.logout()
                resp = self.client.get(url)
                layercap = dlxml.fromstring(resp.content)
                self.assertIsNotNone(layercap)
            finally:
                # annonymous can not download created resource
                self.assertEqual(['view_resourcebase'], self.get_user_resource_perms(saved_dataset, anonymous))
                # Cleanup
                saved_dataset.delete()

        with override_settings(
            DEFAULT_ANONYMOUS_VIEW_PERMISSION=False,
            DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION=True
        ):
            saved_dataset = create_dataset(
                name='san_andres_y_providencia_poi_by_norman',
                title='san_andres_y_providencia_poi',
                owner_name=norman,
                geometry_type='Point'
            )
            # annonymous can view/download created resource
            self.assertEqual(
                ['download_resourcebase', 'view_resourcebase'],
                self.get_user_resource_perms(saved_dataset, anonymous)
            )
            # Cleanup
            saved_dataset.delete()

        with override_settings(
            DEFAULT_ANONYMOUS_VIEW_PERMISSION=False,
            DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION=False
        ):
            saved_dataset = create_dataset(
                name='san_andres_y_providencia_poi_by_norman',
                title='san_andres_y_providencia_poi',
                owner_name=norman,
                geometry_type='Point'
            )
            # annonymous can not view/download created resource
            self.assertEqual([], self.get_user_resource_perms(saved_dataset, anonymous))
            # Cleanup
            saved_dataset.delete()

    def get_user_resource_perms(self, instance, user):
        return list(
            instance.get_user_perms(user).union(instance.get_self_resource().get_user_perms(user))
        )
