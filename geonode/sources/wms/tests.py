#########################################################################
#
# Copyright (C) 2026 OSGeo
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
from unittest.mock import MagicMock, patch

import requests
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from requests.auth import HTTPBasicAuth
from rest_framework.test import APITestCase

from geonode.security.auth_registry import auth_handler_registry
from geonode.sources.base import SourceProviderError
from geonode.sources.models import DataItem
from geonode.sources.registry import source_provider_registry
from geonode.sources.wms.auth import WmsAuthHandler

# RFC 2606 host: the tests never reach a real service, every request is mocked
PAYLOAD = {"url": "https://maps.example.com/wms?map=roads"}

CAPABILITIES_130 = b"""<?xml version="1.0"?>
<WMS_Capabilities version="1.3.0" xmlns="http://www.opengis.net/wms">
  <Service><Name>WMS</Name><Title>Example</Title></Service>
  <Capability>
    <Request><GetCapabilities><Format>text/xml</Format></GetCapabilities></Request>
    <Layer>
      <Title>Root</Title>
      <Layer>
        <Name>ws:roads</Name><Title>Roads</Title><Abstract>Main roads</Abstract>
        <KeywordList><Keyword>transport</Keyword></KeywordList>
        <EX_GeographicBoundingBox>
          <westBoundLongitude>1</westBoundLongitude><eastBoundLongitude>2</eastBoundLongitude>
          <southBoundLatitude>3</southBoundLatitude><northBoundLatitude>4</northBoundLatitude>
        </EX_GeographicBoundingBox>
      </Layer>
      <Layer>
        <Name>ws:group</Name><Title>Group</Title>
        <Layer><Name>ws:rivers</Name></Layer>
      </Layer>
    </Layer>
  </Capability>
</WMS_Capabilities>"""

# GeoServer and most servers declare a DOCTYPE in 1.1.1
CAPABILITIES_111 = b"""<?xml version="1.0"?>
<!DOCTYPE WMT_MS_Capabilities SYSTEM "http://schemas.opengis.net/wms/1.1.1/WMS_MS_Capabilities.dtd"
  [<!ELEMENT VendorSpecificCapabilities EMPTY>]>
<WMT_MS_Capabilities version="1.1.1">
  <Service><Name>OGC:WMS</Name><Title>Example</Title></Service>
  <Capability>
    <Request><GetCapabilities><Format>application/vnd.ogc.wms_xml</Format></GetCapabilities></Request>
    <Layer>
      <Title>Root</Title>
      <Layer><Name>ws:roads</Name><Title>Roads</Title><LatLonBoundingBox minx="1" miny="3" maxx="2" maxy="4"/></Layer>
    </Layer>
  </Capability>
</WMT_MS_Capabilities>"""

CAPABILITIES_XXE = b"""<?xml version="1.0"?>
<!DOCTYPE WMS_Capabilities [<!ENTITY secret SYSTEM "file:///etc/passwd">]>
<WMS_Capabilities version="1.3.0" xmlns="http://www.opengis.net/wms">
  <Service><Name>WMS</Name><Title>Example</Title></Service>
  <Capability><Layer><Title>Root</Title><Layer><Name>ws:roads</Name><Title>&secret;</Title></Layer></Layer></Capability>
</WMS_Capabilities>"""


def response(content, status_code=200):
    _response = MagicMock(content=content, status_code=status_code)
    _response.raise_for_status.side_effect = requests.HTTPError(f"{status_code} error") if status_code >= 400 else None
    return _response


class WmsTestCase(TestCase):
    def setUp(self):
        # is_safe_url resolves the host: the check itself is covered by geonode.utils
        _patcher = patch("geonode.sources.wms.forms.is_safe_url", return_value=True)
        self.is_safe_url = _patcher.start()
        self.addCleanup(_patcher.stop)

    def create_connection(self, **overrides):
        return WmsAuthHandler.create_auth_config({**PAYLOAD, **overrides})


class WmsAuthHandlerTests(WmsTestCase):
    def test_validate_should_fill_the_default_version(self):
        self.assertEqual("1.3.0", WmsAuthHandler.validate(dict(PAYLOAD))["version"])

    def test_validate_should_drop_the_ogc_parameters_and_keep_the_vendor_ones(self):
        """The provider sets service, request and version: a value left in the url would override them"""
        actual = WmsAuthHandler.validate({"url": "https://maps.example.com/wms?map=roads&SERVICE=WMS&Request=GetMap"})
        self.assertEqual("https://maps.example.com/wms?map=roads", actual["url"])

    def test_validate_should_refuse_a_username_without_a_password(self):
        with self.assertRaises(ValidationError) as ctx:
            WmsAuthHandler.validate({**PAYLOAD, "username": "reader"})
        self.assertIn("Provide both username and password, or none.", ctx.exception.messages)

    def test_validate_should_refuse_an_unsafe_url(self):
        self.is_safe_url.return_value = False
        with self.assertRaises(ValidationError):
            WmsAuthHandler.validate({"url": "http://127.0.0.1/wms"})

    def test_validate_should_keep_the_stored_password_when_left_blank(self):
        _connection = self.create_connection(username="reader", password=" s3 cret ")
        actual = WmsAuthHandler.validate({**PAYLOAD, "username": "reader", "password": ""}, instance=_connection)
        self.assertEqual(" s3 cret ", actual["password"])

    def test_get_request_auth_should_be_basic_only_with_credentials(self):
        _public = auth_handler_registry.build(self.create_connection())
        _protected = auth_handler_registry.build(self.create_connection(username="reader", password="secret"))
        self.assertIsNone(_public.get_request_auth())
        self.assertEqual(HTTPBasicAuth("reader", "secret"), _protected.get_request_auth())


@patch("geonode.sources.wms.provider.safe_request_url")
class WmsSourceProviderTests(WmsTestCase):
    def setUp(self):
        super().setUp()
        self.sut = source_provider_registry.get("wms")

    def test_browse_should_return_the_named_leaf_layers(self, safe_request_url):
        """Group layers only collect other layers: their children are the data items"""
        safe_request_url.return_value = response(CAPABILITIES_130)
        actual = self.sut.browse(self.create_connection())
        self.assertListEqual(["wms:?layer=ws%3Aroads", "wms:?layer=ws%3Arivers"], [_entry.uri for _entry in actual])
        self.assertDictEqual(
            {"name": "ws:roads", "abstract": "Main roads", "keywords": ["transport"], "bbox": [1.0, 3.0, 2.0, 4.0]},
            actual[0].details,
        )
        self.assertListEqual(["Roads", "rivers"], [_entry.title for _entry in actual])

    def test_browse_should_request_the_capabilities_with_the_connection_parameters(self, safe_request_url):
        safe_request_url.return_value = response(CAPABILITIES_111)
        self.sut.browse(self.create_connection(version="1.1.1", username="reader", password="secret"))
        safe_request_url.assert_called_once()
        self.assertEqual(("GET", "https://maps.example.com/wms?map=roads"), safe_request_url.call_args.args)
        self.assertDictEqual(
            {"service": "WMS", "request": "GetCapabilities", "version": "1.1.1"},
            safe_request_url.call_args.kwargs["params"],
        )
        self.assertEqual(HTTPBasicAuth("reader", "secret"), safe_request_url.call_args.kwargs["auth"])

    def test_browse_should_read_a_1_1_1_document_with_its_doctype(self, safe_request_url):
        safe_request_url.return_value = response(CAPABILITIES_111)
        actual = self.sut.browse(self.create_connection(version="1.1.1"))
        self.assertListEqual(["wms:?layer=ws%3Aroads"], [_entry.uri for _entry in actual])

    def test_browse_should_never_resolve_external_entities(self, safe_request_url):
        """The entity is left unresolved, so the document is refused instead of carrying a local file"""
        safe_request_url.return_value = response(CAPABILITIES_XXE)
        with self.assertRaises(SourceProviderError):
            self.sut.browse(self.create_connection())

    def test_browse_should_raise_a_provider_error_if_the_service_cannot_be_read(self, safe_request_url):
        for _side_effect in (
            requests.exceptions.InvalidURL("The requested URL is not allowed."),
            requests.ConnectionError("maps.example.com unreachable"),
            response(b"<html>not found</html>", status_code=404),
            response(b"not xml"),
            response(b'<ServiceExceptionReport version="1.3.0"/>'),
        ):
            with self.subTest(side_effect=_side_effect):
                if isinstance(_side_effect, Exception):
                    safe_request_url.side_effect, safe_request_url.return_value = _side_effect, None
                else:
                    safe_request_url.side_effect, safe_request_url.return_value = None, _side_effect
                with self.assertRaises(SourceProviderError):
                    self.sut.browse(self.create_connection())

    def test_test_connection_should_not_expose_the_cause(self, safe_request_url):
        safe_request_url.side_effect = requests.ConnectionError("maps.example.com: connection refused")
        with self.assertLogs("geonode.sources.wms.provider", level="ERROR"):
            success, message = self.sut.test_connection(self.create_connection())
        self.assertFalse(success)
        self.assertNotIn("maps.example.com", message)

    def test_test_connection_should_succeed_on_a_capabilities_document(self, safe_request_url):
        safe_request_url.return_value = response(CAPABILITIES_130)
        self.assertTupleEqual((True, ""), self.sut.test_connection(self.create_connection()))


class WmsApiTests(APITestCase):
    # GeoNode drops sessions without an OAuth token, created on login from these apps
    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

    def setUp(self):
        _patcher = patch("geonode.sources.wms.forms.is_safe_url", return_value=True)
        _patcher.start()
        self.addCleanup(_patcher.stop)
        self.staff = get_user_model().objects.create_user(username="sources_staff", password="password", is_staff=True)
        self.client.force_login(self.staff)

    @patch("geonode.sources.wms.provider.safe_request_url", return_value=response(CAPABILITIES_130))
    def test_creating_a_wms_connection_should_discover_its_layers(self, safe_request_url):
        response_ = self.client.post(
            "/api/v2/source-connections/",
            {"type": "wms", "payload": {**PAYLOAD, "username": "reader", "password": "secret"}},
            format="json",
        )
        self.assertEqual(201, response_.status_code, response_.json())
        _connection = response_.json()["source_connection"]
        self.assertNotIn("password", _connection["connection"])

        self.assertDictEqual({"found": 2, "created": 2, "missing": 0}, response_.json()["discovery"])
        self.assertSetEqual(
            {("wms", "wms:?layer=ws%3Aroads"), ("wms", "wms:?layer=ws%3Arivers")},
            set(DataItem.objects.values_list("source_provider", "uri")),
        )

        response_ = self.client.post(f"/api/v2/source-connections/{_connection['id']}/discover/")
        self.assertEqual(200, response_.status_code, response_.json())
        self.assertDictEqual({"found": 2, "created": 0, "missing": 0}, response_.json())

    @patch("geonode.sources.wms.provider.safe_request_url", side_effect=requests.ConnectionError("down"))
    def test_discover_should_not_expose_the_cause(self, safe_request_url):
        _connection = WmsAuthHandler.create_auth_config(dict(PAYLOAD))
        with self.assertLogs("geonode.sources.api.views", level="ERROR"):
            response_ = self.client.post(f"/api/v2/source-connections/{_connection.pk}/discover/")
        self.assertEqual(502, response_.status_code)
        self.assertDictEqual({"detail": "Could not browse the connection."}, response_.json())
