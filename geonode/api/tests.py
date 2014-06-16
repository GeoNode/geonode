import datetime

from django.core.urlresolvers import reverse
from tastypie.test import ResourceTestCase

from geonode.base.populate_test_data import create_models, all_public
from geonode.layers.models import Layer

from .resourcebase_api import LayerResource, MapResource, DocumentResource, ResourceBaseResource


class PermissionsApiTests(ResourceTestCase):

    fixtures = ['initial_data.json', 'bobby']

    def setUp(self):
        super(PermissionsApiTests, self).setUp()

        self.user = 'admin'
        self.passwd = 'admin'
        self.list_url = reverse('api_dispatch_list', kwargs={'api_name':'api', 'resource_name':'layers'})
        create_models(type='layer')
        all_public()
        self.perm_spec = {"users": {}, "groups": {}}

    def test_layer_get_list_unauth_all_public(self):
        """ 
        Test that the correct number of layers are returned when the
        client is not logged in and all are public
        """

        resp = self.api_client.get(self.list_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 8)

    def test_layers_get_list_unauth_some_public(self):
        """
        Test that if a layer is not public then not all are returned when the
        client is not logged in
        """
        layer = Layer.objects.all()[0]
        layer.set_permissions(self.perm_spec)

        resp = self.api_client.get(self.list_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 7)

    def test_layers_get_list_auth_some_public(self):
        """
        Test that if a layer is not public then all are returned if the
        client is not logged in
        """
        self.api_client.client.login(username=self.user, password=self.passwd)
        layer = Layer.objects.all()[0]
        layer.set_permissions(self.perm_spec)

        resp = self.api_client.get(self.list_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 8)

    def test_layer_get_list_layer_private_to_one_user(self):
        """
        Test that if a layer is only visible by admin, then does not appear in the
        unauthenticated list nor in the list when logged is as bobby
        """
        perm_spec = {"users":{
                "admin": ['view_resourcebase']
            }, "groups":{}}
        layer = Layer.objects.all()[0]
        layer.set_permissions(perm_spec)
        resp = self.api_client.get(self.list_url)
        self.assertEquals(len(self.deserialize(resp)['objects']), 7)

        self.api_client.client.login(username='bobby', password='bob')
        resp = self.api_client.get(self.list_url)
        self.assertEquals(len(self.deserialize(resp)['objects']), 7)

        self.api_client.client.login(username=self.user, password=self.passwd)
        resp = self.api_client.get(self.list_url)
        self.assertEquals(len(self.deserialize(resp)['objects']), 8)

    def test_layer_get_detail_unauth_layer_not_public(self):
        """
        Test that layer detail gives 401 when not public and not logged in
        """
        layer = Layer.objects.all()[0]
        layer.set_permissions(self.perm_spec)
        self.assertHttpUnauthorized(self.api_client.get(
            self.list_url + str(layer.id) + '/'))

        self.api_client.client.login(username=self.user, password=self.passwd)
        resp = self.api_client.get(self.list_url + str(layer.id) +'/')
        self.assertValidJSONResponse(resp)


class SearchApiTests(ResourceTestCase):
    """Test the search"""

    fixtures = ['initial_data.json', 'bobby']

    def setUp(self):
        super(SearchApiTests, self).setUp()

        self.list_url = reverse('api_dispatch_list', kwargs={'api_name':'api', 'resource_name':'layers'})
        create_models(type='layer')
        all_public()

    def test_category_filters(self):
        """Test category filtering"""

        filter_url = self.list_url + '?category__identifier=location'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 3)

        filter_url = self.list_url + '?category__identifier__in=location&category__identifier__in=biota'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 5)

    def test_tag_filters(self):
        """Test keywords filtering"""

        filter_url = self.list_url + '?keywords__slug=layertagunique'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 1)

        filter_url = self.list_url + '?keywords__slug__in=layertagunique&keywords__slug__in=populartag'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 8)

    def test_owner_filters(self):
        """Test owner filtering"""

        filter_url = self.list_url + '?owner__username=user1'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 2)

        filter_url = self.list_url + '?owner__username__in=user1&owner__username__in=foo'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 3)

    def test_title_filter(self):
        """Test title filtering"""

        filter_url = self.list_url + '?title=layer2'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 1)


    def test_date_filter(self):
        """Test date filtering"""

        filter_url = self.list_url + '?date__exact=1985-01-01'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 1)

        filter_url = self.list_url + '?date__gte=1985-01-01'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 3)

        filter_url = self.list_url + '?date__range=1950-01-01,1985-01-01'

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEquals(len(self.deserialize(resp)['objects']), 4)
