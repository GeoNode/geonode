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

from django.conf import settings
from django.urls import reverse
from mock import patch
from rest_framework.test import APITestCase
from guardian.shortcuts import assign_perm, get_anonymous_user

from geonode.base.populate_test_data import create_models
from geonode.layers.models import Dataset
from geonode.maps.models import Map, MapLayer

logger = logging.getLogger(__name__)


class MapsApiTests(APITestCase):

    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

    def setUp(self):
        create_models(b"document")
        create_models(b"map")
        create_models(b"dataset")
        first_map = Map.objects.first()
        first_map.blob = DUMMY_MAPDATA
        first_map.save()
        first_dataset = Dataset.objects.first()
        MapLayer.objects.create(
            map=first_map,
            extra_params={"foo": "bar"},
            name=first_dataset.alternate,
            store=first_dataset.store,
            current_style="some-style",
            local=True,
        )

    def test_maps(self):
        """
        Ensure we can access the Maps list.
        """
        url = reverse("maps-list")
        # Anonymous
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 9)
        # Check: No overfetching for maplayers
        self.assertTrue(any([map.get("maplayers", []) for map in response.data["maps"]]))

        # Pagination
        self.assertEqual(len(response.data["maps"]), 9)
        logger.debug(response.data)

        for _l in response.data["maps"]:
            self.assertTrue(_l["resource_type"], "map")

        # Get Layers List (backgrounds)
        resource = Map.objects.first()
        assign_perm("base.view_resourcebase", get_anonymous_user(), resource.get_self_resource())

        url = urljoin(f"{reverse('maps-detail', kwargs={'pk': resource.pk})}/", "maplayers/")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        layers_data = response.data
        self.assertIsNotNone(layers_data)
        self.assertEqual(layers_data[0]["extra_params"], {"foo": "bar"})
        self.assertIsNotNone(layers_data[0]["dataset"])

        # Get Local-Layers List (GeoNode)
        url = urljoin(f"{reverse('maps-detail', kwargs={'pk': resource.pk})}/", "datasets/")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        layers_data = response.data
        self.assertIsNotNone(layers_data)

        if settings.GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY == "mapstore":
            url = reverse("maps-list")
            self.assertEqual(url, "/api/v2/maps")

            # Anonymous
            response = self.client.get(url, format="json")
            self.assertEqual(response.status_code, 200)
            if response.data:
                self.assertEqual(len(response.data), 5)  # now are 5 since will read from maps

                # Get Full Map layer configuration
                url = reverse("maps-detail", kwargs={"pk": resource.pk})
                response = self.client.get(f"{url}?include[]=data", format="json")
                self.assertEqual(response.status_code, 200)
                self.assertTrue(len(response.data) > 0)
                self.assertTrue("data" in response.data["map"])
                self.assertTrue(len(response.data["map"]["data"]["map"]["layers"]) == 7)
                self.assertEqual(response.data["map"]["maplayers"][0]["extra_params"], {"foo": "bar"})
                self.assertIsNotNone(response.data["map"]["maplayers"][0]["dataset"])

    def test_patch_map(self):
        """
        Patch to maps/<pk>/
        """
        # Get Layers List (backgrounds)
        resource = Map.objects.first()
        url = reverse("maps-detail", kwargs={"pk": resource.pk})

        data = {
            "title": f"{resource.title}-edited",
            "abstract": resource.abstract,
            "data": DUMMY_MAPDATA,
            "id": resource.id,
            "maplayers": DUMMY_MAPLAYERS_DATA,
        }
        self.client.login(username="admin", password="admin")
        response = self.client.patch(f"{url}?include[]=data", data=data, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) > 0)
        self.assertTrue("data" in response.data["map"])
        self.assertTrue(len(response.data["map"]["data"]["map"]["layers"]) == 7)
        response_maplayer = response.data["map"]["maplayers"][0]
        self.assertEqual(response_maplayer["extra_params"], {"msId": "Stamen.Watercolor__0"})
        self.assertEqual(response_maplayer["current_style"], "some-style-first-layer")
        self.assertIsNotNone(response_maplayer["dataset"])

    @patch("geonode.maps.api.views.resolve_object")
    def test_patch_map_raise_exception(self, mocked_obj):
        """
        Patch to maps/<pk>/
        """
        # Get Layers List (backgrounds)
        resource = Map.objects.first()
        mocked_obj.return_value = Map.objects.last()

        url = reverse("maps-detail", kwargs={"pk": resource.pk})

        data = {
            "title": f"{resource.title}-edited",
            "abstract": resource.abstract,
            "data": DUMMY_MAPDATA,
            "id": resource.id,
            "maplayers": DUMMY_MAPLAYERS_DATA,
        }
        self.client.login(username="admin", password="admin")
        response = self.client.patch(f"{url}?include[]=data", data=data, format="json")

        expected_error = {
            "success": False,
            "errors": [
                "serializer instance and object are different"
            ],
            "code": "maps_exception"
        }
        self.assertEqual(response.status_code, 500)
        self.assertEqual(expected_error, response.json())

    def test_create_map(self):
        """
        Post to maps/
        """
        # Get Layers List (backgrounds)
        url = reverse("maps-list")

        data = {
            "title": "Some created map",
            "data": DUMMY_MAPDATA,
            "maplayers": DUMMY_MAPLAYERS_DATA,
        }
        self.client.login(username="admin", password="admin")
        response = self.client.post(f"{url}?include[]=data", data=data, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertTrue(len(response.data) > 0)
        self.assertTrue("data" in response.data["map"])
        self.assertTrue(len(response.data["map"]["data"]["map"]["layers"]) == 7)
        response_maplayer = response.data["map"]["maplayers"][0]
        self.assertEqual(response_maplayer["extra_params"], {"msId": "Stamen.Watercolor__0"})
        self.assertEqual(response_maplayer["current_style"], "some-style-first-layer")
        self.assertIsNotNone(response_maplayer["dataset"])
        self.assertIsNotNone(response.data["map"]['thumbnail_url'])


DUMMY_MAPDATA = {
    "map": {
        "zoom": 9,
        "units": "m",
        "center": {"x": 11.763505157657004, "y": 43.7880264429571, "crs": "EPSG:4326"},
        "groups": [{"id": "Default", "title": "Default", "expanded": True}],
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
                "styles": ["some-style-first-layer", "some-other-style-first-layer"],
                "singleTile": False,
                "visibility": False,
                "extraParams": {"msId": "Stamen.Watercolor__0"},
                "hideLoading": False,
                "useForElevation": False,
                "handleClickOnLayer": False,
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
                "extraParams": {"msId": "Stamen.Terrain__1"},
                "hideLoading": False,
                "useForElevation": False,
                "handleClickOnLayer": False,
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
                "extraParams": {"msId": "Stamen.Toner__2"},
                "hideLoading": False,
                "useForElevation": False,
                "handleClickOnLayer": False,
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
                "extraParams": {"msId": "mapnik__3"},
                "hideLoading": False,
                "useForElevation": False,
                "handleClickOnLayer": False,
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
                "extraParams": {"msId": "OpenTopoMap__4"},
                "hideLoading": False,
                "useForElevation": False,
                "handleClickOnLayer": False,
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
                "extraParams": {"msId": "s2cloudless"},
                "hideLoading": False,
                "useForElevation": False,
                "handleClickOnLayer": False,
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
                "extraParams": {"msId": "none"},
                "hideLoading": False,
                "useForElevation": False,
                "handleClickOnLayer": False,
            },
        ],
        "maxExtent": [-20037508.34, -20037508.34, 20037508.34, 20037508.34],
        "mapOptions": {},
        "projection": "EPSG:3857",
        "backgrounds": [],
    },
    "version": 2,
    "timelineData": {},
    "dimensionData": {},
    "widgetsConfig": {"layouts": {"md": [], "xxs": []}},
    "catalogServices": {
        "services": {
            "GeoNode Catalogue": {
                "url": "http://localhost:8000/catalogue/csw",
                "type": "csw",
                "title": "GeoNode Catalogue",
                "autoload": True,
            },
        },
        "selectedService": "GeoNode Catalogue",
    },
    "mapInfoConfiguration": {},
}

DUMMY_MAPLAYERS_DATA = [
    {
        "extra_params": {"msId": "Stamen.Watercolor__0"},
        "current_style": "some-style-first-layer",
        "name": "geonode:CA",
    }
]
