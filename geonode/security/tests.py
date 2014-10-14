import json

from django.core.urlresolvers import reverse
from django.test.client import Client
from tastypie.test import ResourceTestCase
from guardian.shortcuts import assign_perm

from geonode.base.populate_test_data import create_models, all_public
from geonode.layers.models import Layer
from geonode.people.models import Profile


class BulkPermissionsTests(ResourceTestCase):
    fixtures = ['initial_data.json', 'bobby']

    def setUp(self):
        super(BulkPermissionsTests, self).setUp()

        self.user = 'admin'
        self.passwd = 'admin'
        self.list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers'})
        self.bulk_perms_url = reverse('bulk_permissions')
        create_models(type='layer')
        all_public()
        self.perm_spec = {
            "users": {"admin": ["view_resourcebase"]}, "groups": {}}

    def test_set_bulk_permissions(self):
        """Test that after restrict view permissions on two layers
        bobby is unable to see them"""

        c = Client()
        layers = Layer.objects.all()[:2].values_list('id', flat=True)
        layers_id = map(lambda x: str(x), layers)

        c.login(username='admin', password='admin')
        resp = c.get(self.list_url)
        self.assertEquals(len(self.deserialize(resp)['objects']), 8)
        data = {
            'permissions': json.dumps(self.perm_spec),
            'resources': layers_id
        }
        resp = c.post(self.bulk_perms_url, data)
        self.assertHttpOK(resp)
        c.logout()

        c.login(username='bobby', password='bob')
        resp = c.get(self.list_url)
        self.assertEquals(len(self.deserialize(resp)['objects']), 6)

    def test_bobby_cannot_set_all(self):
        """Test that Bobby can set the permissions only only on the ones
        for which he has the right"""

        layer = Layer.objects.all()[0]
        c = Client()
        c.login(username='admin', password='admin')
        # give bobby the right to change the layer permissions
        assign_perm('change_resourcebase', Profile.objects.get(username='bobby'), layer.get_self_resource())
        c.logout()
        c.login(username='bobby', password='bob')
        layer2 = Layer.objects.all()[1]
        data = {
            'permissions': json.dumps({"users": {"bobby": ["view_resourcebase"]}, "groups": {}}),
            'resources': [layer.id, layer2.id]
        }
        resp = c.post(self.bulk_perms_url, data)
        self.assertTrue(layer2.title in json.loads(resp.content)['not_changed'])
