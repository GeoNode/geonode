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
import logging
import shutil
import tempfile
from unittest.mock import patch
from django.conf import settings
from django.test import override_settings

import gisdata
from django.conf.urls import url
from django.contrib.auth import get_user_model
from django.urls import reverse
from geonode import geoserver
from geonode.base.populate_test_data import create_models
from geonode.geoserver.createlayer.utils import create_layer
from geonode.layers.models import Layer
from geonode.utils import check_ogc_backend
from rest_framework.test import APITestCase, URLPatternsTestCase

logger = logging.getLogger(__name__)


class LayersApiTests(APITestCase, URLPatternsTestCase):

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

    from geonode.urls import urlpatterns

    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        from geonode.geoserver.views import layer_acls, resolve_user
        urlpatterns += [
            url(r'^acls/?$', layer_acls, name='layer_acls'),
            url(r'^acls_dep/?$', layer_acls, name='layer_acls_dep'),
            url(r'^resolve_user/?$', resolve_user, name='layer_resolve_user'),
            url(r'^resolve_user_dep/?$', resolve_user, name='layer_resolve_user_dep'),
        ]

    def setUp(self):
        create_models(b'document')
        create_models(b'map')
        create_models(b'layer')

    def tearDown(self) -> None:
        Layer.objects.filter(name='new_name').delete()

    def test_layers(self):
        """
        Ensure we can access the Layers list.
        """
        url = reverse('layers-list')
        # Anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 8)
        # Pagination
        self.assertEqual(len(response.data['layers']), 8)
        logger.debug(response.data)

        for _l in response.data['layers']:
            self.assertTrue(_l['resource_type'], 'layer')

    def test_raw_HTML_stripped_properties(self):
        """
        Ensure "raw_*" properties returns no HTML or carriage-return tag
        """
        layer = Layer.objects.first()
        layer.abstract = "<p><em>No abstract provided</em>.</p>\r\n<p><img src=\"data:image/jpeg;base64,/9j/4AAQSkZJR/>"
        layer.constraints_other = "<p><span style=\"text-decoration: underline;\">None</span></p>"
        layer.supplemental_information = "<p>No information provided &iacute;</p> <p>&pound;682m</p>"
        layer.data_quality_statement = "<p><strong>OK</strong></p>\r\n<table style=\"border-collapse: collapse; width:\
            85.2071%;\" border=\"1\">\r\n<tbody>\r\n<tr>\r\n<td style=\"width: 49.6528%;\">1</td>\r\n<td style=\"width:\
            50%;\">2</td>\r\n</tr>\r\n<tr>\r\n<td style=\"width: 49.6528%;\">a</td>\r\n<td style=\"width: 50%;\">b</td>\
            \r\n</tr>\r\n</tbody>\r\n</table>"
        layer.save()

        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))

        url = reverse('layers-detail', kwargs={'pk': layer.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.data['layer']['pk']), int(layer.pk))
        self.assertEqual(response.data['layer']['raw_abstract'], "No abstract provided.")
        self.assertEqual(response.data['layer']['raw_constraints_other'], "None")
        self.assertEqual(response.data['layer']['raw_supplemental_information'], "No information provided í £682m")
        self.assertEqual(response.data['layer']['raw_data_quality_statement'], "OK    1 2   a b")

    def test_layer_replace_anonymous_should_raise_error(self):
        layer = Layer.objects.first()
        url = reverse("layers-replace-layer", args=(layer.id,))

        expected = {"detail": "Authentication credentials were not provided."}

        response = self.client.put(url)
        self.assertEqual(403, response.status_code)
        self.assertDictEqual(expected, response.json())

    def test_layer_replace_should_redirect_for_not_accepted_method(self):
        layer = Layer.objects.first()
        url = reverse("layers-replace-layer", args=(layer.id,))
        self.client.login(username="admin", password="admin")

        response = self.client.post(url)
        self.assertEqual(405, response.status_code)

        response = self.client.get(url)
        self.assertEqual(405, response.status_code)

        response = self.client.patch(url)
        self.assertEqual(405, response.status_code)

    def test_layer_replace_should_raise_error_if_layer_does_not_exists(self):
        url = reverse("layers-replace-layer", args=(999999999999999,))

        expected = {"detail": "Layer with ID 999999999999999 is not available"}

        self.client.login(username="admin", password="admin")

        response = self.client.put(url)
        self.assertEqual(404, response.status_code)
        self.assertDictEqual(expected, response.json())

    @patch("geonode.layers.views.validate_input_source")
    @override_settings(ASYNC_SIGNALS=False)
    def test_layer_replace_should_work(self, _validate_input_source):

        _validate_input_source.return_value = True

        admin = get_user_model().objects.get(username='admin')

        layer = create_layer(
            "new_name",
            "new_name",
            admin,
            "Point",
        )
        cnt = Layer.objects.count()

        self.assertEqual('No abstract provided', layer.abstract)
        self.assertEqual(Layer.objects.count(), cnt)

        layer.refresh_from_db()
        logger.error(layer.alternate)
        # renaming the file in the same way as the layer name
        # the filename must be consistent with the layer name
        tempdir = tempfile.mkdtemp(dir=settings.STATIC_ROOT)

        shutil.copyfile(f"{gisdata.GOOD_DATA}/vector/single_point.shp", f"{tempdir}/{layer.alternate.split(':')[1]}.shp")
        shutil.copyfile(f"{gisdata.GOOD_DATA}/vector/single_point.dbf", f"{tempdir}/{layer.alternate.split(':')[1]}.dbf")
        shutil.copyfile(f"{gisdata.GOOD_DATA}/vector/single_point.prj", f"{tempdir}/{layer.alternate.split(':')[1]}.prj")
        shutil.copyfile(f"{gisdata.GOOD_DATA}/vector/single_point.shx", f"{tempdir}/{layer.alternate.split(':')[1]}.shx")
        shutil.copyfile(f"{settings.PROJECT_ROOT}/base/fixtures/test_xml.xml", f"{tempdir}/{layer.alternate.split(':')[1]}.xml")

        payload = {
            "permissions": '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            "time": "false",
            "charset": "UTF-8",
            "store_spatial_files": False,
            "base_file_path": f"{tempdir}/{layer.alternate.split(':')[1]}.shp",
            "dbf_file_path": f"{tempdir}/{layer.alternate.split(':')[1]}.dbf",
            "prj_file_path": f"{tempdir}/{layer.alternate.split(':')[1]}.prj",
            "shx_file_path": f"{tempdir}/{layer.alternate.split(':')[1]}.shx",
            "xml_file_path": f"{tempdir}/{layer.alternate.split(':')[1]}.xml"
        }

        url = reverse("layers-replace-layer", args=(layer.id,))

        self.client.login(username="admin", password="admin")

        response = self.client.put(url, data=payload)
        self.assertEqual(200, response.status_code)

        layer.refresh_from_db()
        # evaluate that the abstract is updated and the number of available layer is not changed
        self.assertEqual(Layer.objects.count(), cnt)
        self.assertEqual('real abstract', layer.abstract)

        if tempdir:
            shutil.rmtree(tempdir)
