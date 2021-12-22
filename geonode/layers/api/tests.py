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

from urllib.parse import urljoin

from django.urls import reverse
from rest_framework.test import APITestCase

from geonode.layers.models import Dataset, Attribute
from geonode.base.populate_test_data import create_models
from geonode.maps.models import Map, MapLayer

logger = logging.getLogger(__name__)


class DatasetsApiTests(APITestCase):

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

    def setUp(self):
        create_models(b'document')
        create_models(b'map')
        create_models(b'dataset')

    def test_datasets(self):
        """
        Ensure we can access the Layers list.
        """
        url = reverse('datasets-list')
        # Anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 8)

        # Pagination
        self.assertEqual(len(response.data['datasets']), 8)
        logger.debug(response.data)

        for _l in response.data['datasets']:
            self.assertTrue(_l['resource_type'], 'dataset')
        # Test list response doesn't have attribute_set
        self.assertIsNotNone(response.data['datasets'][0].get('ptype'))
        self.assertIsNone(response.data['datasets'][0].get('attribute_set'))
        self.assertIsNone(response.data['datasets'][0].get('featureinfo_custom_template'))

        _dataset = Dataset.objects.first()

        # Test detail response has attribute_set
        url = urljoin(f"{reverse('datasets-list')}/", f"{_dataset.pk}")
        response = self.client.get(url, format='json')
        self.assertIsNotNone(response.data['dataset'].get('ptype'))
        self.assertIsNotNone(response.data['dataset'].get('subtype'))
        self.assertIsNotNone(response.data['dataset'].get('attribute_set'))

        # Test "featureinfo_custom_template"
        _attribute, _ = Attribute.objects.get_or_create(dataset=_dataset, attribute='name')
        try:
            _attribute.visible = True
            _attribute.attribute_type = Attribute.TYPE_PROPERTY
            _attribute.description = "The Name"
            _attribute.attribute_label = "Name"
            _attribute.display_order = 1
            _attribute.save()

            url = urljoin(f"{reverse('datasets-list')}/", f"{_dataset.pk}")
            response = self.client.get(url, format='json')
            self.assertIsNotNone(response.data['dataset'].get('featureinfo_custom_template'))
            self.assertEqual(
                response.data['dataset'].get('featureinfo_custom_template'),
                '<div><div class="row"><div class="col-xs-6" style="font-weight: bold; word-wrap: break-word;">Name:</div>\
                             <div class="col-xs-6" style="word-wrap: break-word;">${properties.name}</div></div></div>')

            _dataset.featureinfo_custom_template = '<div>Foo Bar</div>'
            _dataset.save()
            url = urljoin(f"{reverse('datasets-list')}/", f"{_dataset.pk}")
            response = self.client.get(url, format='json')
            self.assertIsNotNone(response.data['dataset'].get('featureinfo_custom_template'))
            self.assertEqual(
                response.data['dataset'].get('featureinfo_custom_template'),
                '<div><div class="row"><div class="col-xs-6" style="font-weight: bold; word-wrap: break-word;">Name:</div>\
                             <div class="col-xs-6" style="word-wrap: break-word;">${properties.name}</div></div></div>')

            _dataset.use_featureinfo_custom_template = True
            _dataset.save()
            url = urljoin(f"{reverse('datasets-list')}/", f"{_dataset.pk}")
            response = self.client.get(url, format='json')
            self.assertIsNotNone(response.data['dataset'].get('featureinfo_custom_template'))
            self.assertEqual(
                response.data['dataset'].get('featureinfo_custom_template'),
                '<div>Foo Bar</div>')
        finally:
            _attribute.delete()
            _dataset.featureinfo_custom_template = None
            _dataset.use_featureinfo_custom_template = False
            _dataset.save()

    def test_get_dataset_related_maps_and_maplayers(self):
        dataset = Dataset.objects.first()
        url = reverse('datasets-detail', kwargs={'pk': dataset.pk})
        response = self.client.get(f'{url}/maplayers', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

        response = self.client.get(f'{url}/maplayers', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

        response = self.client.get(f'{url}/maps', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)
        map = Map.objects.first()
        map_layer = MapLayer.objects.create(
                map=map,
                extra_params={},
                name=dataset.alternate,
                store=None,
                current_style=None,
                ows_url=None,
                local=True,
                dataset=dataset
            )
        response = self.client.get(f'{url}/maplayers', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['pk'], map_layer.pk)

        response = self.client.get(f'{url}/maps', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['pk'], map.pk)

    def test_raw_HTML_stripped_properties(self):
        """
        Ensure "raw_*" properties returns no HTML or carriage-return tag
        """
        dataset = Dataset.objects.first()
        dataset.abstract = "<p><em>No abstract provided</em>.</p>\r\n<p><img src=\"data:image/jpeg;base64,/9j/4AAQSkZJR/>"
        dataset.constraints_other = "<p><span style=\"text-decoration: underline;\">None</span></p>"
        dataset.supplemental_information = "<p>No information provided &iacute;</p> <p>&pound;682m</p>"
        dataset.data_quality_statement = "<p><strong>OK</strong></p>\r\n<table style=\"border-collapse: collapse; width:\
            85.2071%;\" border=\"1\">\r\n<tbody>\r\n<tr>\r\n<td style=\"width: 49.6528%;\">1</td>\r\n<td style=\"width:\
            50%;\">2</td>\r\n</tr>\r\n<tr>\r\n<td style=\"width: 49.6528%;\">a</td>\r\n<td style=\"width: 50%;\">b</td>\
            \r\n</tr>\r\n</tbody>\r\n</table>"
        dataset.save()

        # Admin
        self.assertTrue(self.client.login(username='admin', password='admin'))

        url = reverse('datasets-detail', kwargs={'pk': dataset.pk})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.data['dataset']['pk']), int(dataset.pk))
        self.assertEqual(response.data['dataset']['raw_abstract'], "No abstract provided.")
        self.assertEqual(response.data['dataset']['raw_constraints_other'], "None")
        self.assertEqual(response.data['dataset']['raw_supplemental_information'], "No information provided í £682m")
        self.assertEqual(response.data['dataset']['raw_data_quality_statement'], "OK    1 2   a b")
