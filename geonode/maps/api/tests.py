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
from rest_framework.test import APITestCase

from django.conf import settings
from django.urls import reverse

from geonode.maps.models import Map
from geonode.base.populate_test_data import create_models

logger = logging.getLogger(__name__)


class MapsApiTests(APITestCase):

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

    def setUp(self):
        create_models(b'document')
        create_models(b'map')
        create_models(b'layer')
        first = Map.objects.first()
        first.blob = DUMMY_MAPDATA
        first.save()

    def test_maps(self):
        """
        Ensure we can access the Maps list.
        """
        url = reverse('maps-list')
        # Anonymous
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 9)
        # Pagination
        self.assertEqual(len(response.data['maps']), 9)
        logger.debug(response.data)

        for _l in response.data['maps']:
            self.assertTrue(_l['resource_type'], 'map')

        # Get Layers List (backgrounds)
        resource = Map.objects.first()

        url = urljoin(f"{reverse('maps-detail', kwargs={'pk': resource.pk})}/", 'layers/')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        layers_data = response.data
        self.assertIsNotNone(layers_data)

        # Get Local-Layers List (GeoNode)
        url = urljoin(f"{reverse('maps-detail', kwargs={'pk': resource.pk})}/", 'local_layers/')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        layers_data = response.data
        self.assertIsNotNone(layers_data)

        if settings.GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY == 'mapstore':
            url = reverse('maps-list')
            self.assertEqual(url, '/api/v2/maps')

            # Anonymous
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, 200)
            if response.data:
                self.assertEqual(len(response.data), 5)  # now are 5 since will read from maps

                # Get Full Map layer configuration
                url = reverse('maps-detail', kwargs={'pk': resource.pk})
                response = self.client.get(f"{url}?include[]=data", format='json')
                self.assertEqual(response.status_code, 200)
                self.assertTrue(len(response.data) > 0)
                self.assertTrue('data' in response.data['map'])
                self.assertTrue(len(response.data['map']['data']['map']['layers']) == 7)


DUMMY_MAPDATA = {
    "map": {
        "zoom": 9,
        "units": "m",
        "center": {
            "x": 11.763505157657004,
            "y": 43.7880264429571,
            "crs": "EPSG:4326"
        },
        "groups": [
            {
                "id": "Default",
                "title": "Default",
                "expanded": True
            }
        ],
        "layers": [
            {
                "id": "Stamen.Watercolor__0",
                "name": "Stamen.Watercolor",
                "type": "tileprovider",
                "group": "background",
                "title": "Stamen Watercolor",
                "hidden": False,
                "source": "Stamen",
                "provider": "Stamen.Watercolor",
                "thumbURL": "https://stamen-tiles-c.a.ssl.fastly.net/watercolor/0/0/0.jpg",
                "dimensions": [],
                "singleTile": False,
                "visibility": False,
                "extraParams": {
                    "msId": "Stamen.Watercolor__0"
                },
                "hideLoading": False,
                "useForElevation": False,
                "handleClickOnLayer": False
            },
            {
                "id": "Stamen.Terrain__1",
                "name": "Stamen.Terrain",
                "type": "tileprovider",
                "group": "background",
                "title": "Stamen Terrain",
                "hidden": False,
                "source": "Stamen",
                "provider": "Stamen.Terrain",
                "thumbURL": "https://stamen-tiles-d.a.ssl.fastly.net/terrain/0/0/0.png",
                "dimensions": [],
                "singleTile": False,
                "visibility": False,
                "extraParams": {
                    "msId": "Stamen.Terrain__1"
                },
                "hideLoading": False,
                "useForElevation": False,
                "handleClickOnLayer": False
            },
            {
                "id": "Stamen.Toner__2",
                "name": "Stamen.Toner",
                "type": "tileprovider",
                "group": "background",
                "title": "Stamen Toner",
                "hidden": False,
                "source": "Stamen",
                "provider": "Stamen.Toner",
                "thumbURL": "https://stamen-tiles-d.a.ssl.fastly.net/toner/0/0/0.png",
                "dimensions": [],
                "singleTile": False,
                "visibility": False,
                "extraParams": {
                    "msId": "Stamen.Toner__2"
                },
                "hideLoading": False,
                "useForElevation": False,
                "handleClickOnLayer": False
            },
            {
                "id": "mapnik__3",
                "name": "mapnik",
                "type": "osm",
                "group": "background",
                "title": "Open Street Map",
                "hidden": False,
                "source": "osm",
                "dimensions": [],
                "singleTile": False,
                "visibility": True,
                "extraParams": {
                    "msId": "mapnik__3"
                },
                "hideLoading": False,
                "useForElevation": False,
                "handleClickOnLayer": False
            },
            {
                "id": "OpenTopoMap__4",
                "name": "OpenTopoMap",
                "type": "tileprovider",
                "group": "background",
                "title": "OpenTopoMap",
                "hidden": False,
                "source": "OpenTopoMap",
                "provider": "OpenTopoMap",
                "dimensions": [],
                "singleTile": False,
                "visibility": False,
                "extraParams": {
                    "msId": "OpenTopoMap__4"
                },
                "hideLoading": False,
                "useForElevation": False,
                "handleClickOnLayer": False
            },
            {
                "id": "s2cloudless",
                "url": "https://maps.geo-solutions.it/geoserver/wms",
                "name": "s2cloudless:s2cloudless",
                "type": "wms",
                "group": "background",
                "title": "Sentinel-2 cloudless - https://s2maps.eu",
                "format": "image/jpeg",
                "hidden": False,
                "thumbURL": "http://localhost:8000/static/mapstorestyle/img/s2cloudless-s2cloudless.png",
                "dimensions": [],
                "singleTile": False,
                "visibility": False,
                "extraParams": {
                    "msId": "s2cloudless"
                },
                "hideLoading": False,
                "useForElevation": False,
                "handleClickOnLayer": False
            },
            {
                "id": "none",
                "name": "empty",
                "type": "empty",
                "group": "background",
                "title": "Empty Background",
                "hidden": False,
                "source": "ol",
                "dimensions": [],
                "singleTile": False,
                "visibility": False,
                "extraParams": {
                    "msId": "none"
                },
                "hideLoading": False,
                "useForElevation": False,
                "handleClickOnLayer": False
            }
        ],
        "maxExtent": [
            -20037508.34,
            -20037508.34,
            20037508.34,
            20037508.34
        ],
        "mapOptions": {},
        "projection": "EPSG:3857",
        "backgrounds": []
    },
    "version": 2,
    "timelineData": {},
    "dimensionData": {},
    "widgetsConfig": {
        "layouts": {
            "md": [],
            "xxs": []
        }
    },
    "catalogServices": {
        "services": {
            "Demo WMS Service": {
                "url": "https://demo.geo-solutions.it/geoserver/wms",
                "type": "wms",
                "title": "Demo WMS Service",
                "autoload": False
            },
            "Demo WMTS Service": {
                "url": "https://demo.geo-solutions.it/geoserver/gwc/service/wmts",
                "type": "wmts",
                "title": "Demo WMTS Service",
                "autoload": False
            },
            "GeoNode Catalogue": {
                "url": "http://localhost:8000/catalogue/csw",
                "type": "csw",
                "title": "GeoNode Catalogue",
                "autoload": True
            }
        },
        "selectedService": "GeoNode Catalogue"
    },
    "mapInfoConfiguration": {}
}
