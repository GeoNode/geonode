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

"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""
import json
import io
import zipfile

from urllib.parse import urljoin

from django.conf import settings
from geonode.assets.utils import create_asset_and_link
from geonode.proxy.templatetags.proxy_lib_tags import original_link_available
from django.test.client import RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

from geonode.upload.models import Upload

try:
    from unittest.mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test.utils import override_settings

from geonode import geoserver
from geonode.base.models import Link
from geonode.layers.models import Dataset
from geonode.decorators import on_ogc_backend
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.base.populate_test_data import create_models, create_single_dataset
from geonode.proxy.utils import ProxyUrlsRegistry

TEST_DOMAIN = ".github.com"
TEST_URL = f"https://help{TEST_DOMAIN}/"


class ProxyTest(GeoNodeBaseTestSupport):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.admin = get_user_model().objects.get(username="admin")
        create_models(type="dataset")

        # FIXME(Ariel): These tests do not work when the computer is offline.
        self.proxy_url = "/proxy/"
        self.url = TEST_URL

    @patch("geonode.proxy.views.proxy_urls_registry", ProxyUrlsRegistry().set([TEST_DOMAIN]))
    def test_proxy_allowed_host(self):
        """If PROXY_ALLOWED_HOSTS is not empty and DEBUG is False requests should return no error."""
        self.client.login(username="admin", password="admin")
        response = self.client.get(f"{self.proxy_url}?url={self.url}")
        self.assertNotEqual(response.status_code, 403, response.status_code)

    @override_settings(PROXY_ALLOWED_PARAMS_NEEDLES=("request=GetCapabilities",))
    @patch("geonode.proxy.views.proxy_urls_registry", ProxyUrlsRegistry().clear())
    def test_proxy_allowed_params(self):
        response = self.client.get(f"{self.proxy_url}?url=https://example.com?request=GetCapabilities")
        self.assertNotEqual(response.status_code, 403, response.status_code)

    @override_settings(PROXY_ALLOWED_PARAMS_NEEDLES=("request=GetCapabilities",))
    @patch("geonode.proxy.views.proxy_urls_registry", ProxyUrlsRegistry().clear())
    def test_proxy_not_allowed_params(self):
        response = self.client.get(f"{self.proxy_url}?url=http://example.com?param=any")
        self.assertEqual(response.status_code, 403, response.status_code)

    @override_settings(PROXY_ALLOWED_PATH_NEEDLES=("tms",))
    @patch("geonode.proxy.views.proxy_urls_registry", ProxyUrlsRegistry().clear())
    def test_proxy_allowed_path(self):
        response = self.client.get(f"{self.proxy_url}?url=https://example.com/tms/")
        self.assertNotEqual(response.status_code, 403, response.status_code)

    @override_settings(PROXY_ALLOWED_PATH_NEEDLES=("tms",))
    @patch("geonode.proxy.views.proxy_urls_registry", ProxyUrlsRegistry().clear())
    def test_proxy_not_allowed_path(self):
        response = self.client.get(f"{self.proxy_url}?url=http://example.com/xyz")
        self.assertEqual(response.status_code, 403, response.status_code)

    @override_settings(PROXY_ALLOWED_PARAMS_NEEDLES=(), PROXY_ALLOWED_PATH_NEEDLES=())
    # @patch("geonode.proxy.views.proxy_urls_registry", ProxyUrlsRegistry().clear())
    def test_validate_remote_links_hosts(self):
        """If PROXY_ALLOWED_HOSTS is empty and DEBUG is False requests should return 200
        for Remote Services hosts."""
        from geonode.base.models import Link

        dataset = Dataset.objects.all().first()
        dataset.sourcetype = "REMOTE"
        dataset.save()

        link, _ = Link.objects.get_or_create(
            link_type="OGC:WMS",
            resource=dataset,
            extension="html",
            name="WMS",
            mime="text/html",
            url="http://bogus.pocus.com/ows",
        )
        response = self.client.get(f"{self.proxy_url}?url=http://bogus.pocus.com/ows")
        self.assertNotEqual(response.status_code, 403, response.status_code)

        # The service should be removed from the proxy registry
        link.delete()
        response = self.client.get(f"{self.proxy_url}?url=http://bogus.pocus.com/ows")
        self.assertEqual(response.status_code, 403, response.status_code)

    @patch("geonode.proxy.views.proxy_urls_registry", ProxyUrlsRegistry().set([".example.org"]))
    def test_relative_urls(self):
        """Proxying to a URL with a relative path element should normalise the path into
        an absolute path before calling the remote URL."""
        import geonode.proxy.views

        class Response:
            status_code = 200
            content = "Hello World"
            headers = {"Content-Type": "text/html"}

        request_mock = MagicMock()
        request_mock.return_value = (Response(), None)

        geonode.proxy.views.http_client.request = request_mock
        url = "http://example.org/test/test/../../index.html"

        self.client.get(f"{self.proxy_url}?url={url}")
        assert request_mock.call_args[0][0] == "http://example.org/index.html"

    @patch("geonode.proxy.views.proxy_urls_registry", ProxyUrlsRegistry().set(["example.org"]))
    def test_proxy_preserve_headers(self):
        """The GeoNode Proxy should preserve the original request headers."""
        import geonode.proxy.views

        _test_headers = {
            "Access-Control-Allow-Credentials": False,
            "Access-Control-Allow-Headers": "Content-Type, Accept, Authorization, Origin, User-Agent",
            "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, OPTIONS",
            "Cache-Control": "public, must-revalidate, max-age = 30",
            "Connection": "keep-alive",
            "Content-Language": "en",
            "Content-Length": 116559,
            "Content-Type": "image/tiff",
            "Content-Disposition": 'attachment; filename="filename.tif"',
            "Date": "Fri, 05 Nov 2021 17: 19: 11 GMT",
            "Server": "nginx/1.17.2",
            "Set-Cookie": "sessionid = bogus-pocus; HttpOnly; Path=/; SameSite=Lax",
            "Strict-Transport-Security": "max-age=3600; includeSubDomains",
            "Vary": "Authorization, Accept-Language, Cookie, origin",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
        }

        class Response:
            status_code = 200
            content = "Hello World"
            headers = _test_headers

        request_mock = MagicMock()
        request_mock.return_value = (Response(), None)

        geonode.proxy.views.http_client.request = request_mock
        url = "http://example.org/test/test/../../image.tiff"

        response = self.client.get(f"{self.proxy_url}?url={url}")
        self.assertDictContainsSubset(
            {
                "Content-Type": "image/tiff",
                "Vary": "Authorization, Accept-Language, Cookie, origin",
                "X-Content-Type-Options": "nosniff",
                "X-XSS-Protection": "1; mode=block",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Cross-Origin-Opener-Policy": "same-origin",
                "X-Frame-Options": "SAMEORIGIN",
                "Content-Language": "en",
                "Content-Length": "11",
                "Content-Disposition": 'attachment; filename="filename.tif"',
            },
            dict(response.headers.copy()),
        )

    def test_proxy_url_forgery(self):
        import geonode.proxy.views
        from urllib.parse import urlsplit

        class Response:
            status_code = 200
            content = "Hello World"
            headers = {
                "Content-Type": "text/plain",
                "Vary": "Authorization, Accept-Language, Cookie, origin",
                "X-Content-Type-Options": "nosniff",
                "X-XSS-Protection": "1; mode=block",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "X-Frame-Options": "SAMEORIGIN",
                "Content-Language": "en-us",
                "Content-Length": "119",
                "Content-Disposition": 'attachment; filename="filename.tif"',
            }

        request_mock = MagicMock()
        request_mock.return_value = (Response(), None)

        # Non-Legit requests attempting SSRF
        geonode.proxy.views.http_client.request = request_mock
        url = f"http://example.org\\@%23{urlsplit(settings.SITEURL).hostname}"

        response = self.client.get(f"{self.proxy_url}?url={url}")
        self.assertEqual(response.status_code, 403)

        url = f"http://125.126.127.128\\@%23{urlsplit(settings.SITEURL).hostname}"

        response = self.client.get(f"{self.proxy_url}?url={url}")
        self.assertEqual(response.status_code, 403)

        url = f"{settings.SITEURL.rstrip('/')}@db/"

        response = self.client.get(f"{self.proxy_url}?url={url}")
        self.assertEqual(response.status_code, 403)

        url = f"{settings.SITEURL.rstrip('/')}%40db/"

        response = self.client.get(f"{self.proxy_url}?url={url}")
        self.assertEqual(response.status_code, 403)

        # Legit requests using the local host (SITEURL)
        url = f"/\\@%23{urlsplit(settings.SITEURL).hostname}"

        response = self.client.get(f"{self.proxy_url}?url={url}")
        self.assertEqual(response.status_code, 200)

        url = f"{settings.SITEURL}\\@%23{urlsplit(settings.SITEURL).hostname}"

        response = self.client.get(f"{self.proxy_url}?url={url}")
        self.assertEqual(response.status_code, 200)


class DownloadResourceTestCase(GeoNodeBaseTestSupport):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        create_models(type="dataset")

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_download_url_with_not_existing_file(self):
        dataset = Dataset.objects.all().first()
        self.client.login(username="admin", password="admin")
        # ... all should be good
        response = self.client.get(reverse("download", args=(dataset.id,)))
        # Espected 404 since there are no files available for this layer
        self.assertEqual(response.status_code, 404)
        content = response.content
        if isinstance(content, bytes):
            content = content.decode("UTF-8")
        data = content
        self.assertTrue("No files have been found for this resource. Please, contact a system administrator." in data)

    @patch("geonode.storage.manager.storage_manager.exists")
    @patch("geonode.storage.manager.storage_manager.open")
    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_download_url_with_existing_files(self, fopen, fexists):
        fexists.return_value = True
        fopen.return_value = SimpleUploadedFile("foo_file.shp", b"scc")
        dataset = Dataset.objects.all().first()

        dataset_files = [
            f"{settings.PROJECT_ROOT}/assets/tests/data/one.json",
        ]

        asset, link = create_asset_and_link(
            dataset, get_user_model().objects.get(username="admin"), dataset_files, clone_files=False
        )

        dataset.save()

        dataset.refresh_from_db()

        upload = Upload.objects.create(state="RUNNING", resource=dataset)

        assert upload

        self.client.login(username="admin", password="admin")
        # ... all should be good
        response = self.client.get(reverse("download", args=(dataset.id,)))
        # Espected 404 since there are no files available for this layer
        self.assertEqual(response.status_code, 200)
        self.assertEqual("application/zip", response.headers.get("Content-Type"))
        self.assertEqual("attachment; filename=CA.zip", response.headers.get("Content-Disposition"))

        link.delete()
        asset.delete()

    @patch("geonode.storage.manager.storage_manager.exists")
    @patch("geonode.storage.manager.storage_manager.open")
    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_download_files(self, fopen, fexists):
        fexists.return_value = True
        fopen.return_value = SimpleUploadedFile("foo_file.shp", b"scc")
        dataset = Dataset.objects.all().first()

        dataset_files = [
            f"{settings.PROJECT_ROOT}/assets/tests/data/one.json",
        ]

        asset, link = create_asset_and_link(
            dataset, get_user_model().objects.get(username="admin"), dataset_files, clone_files=False
        )

        dataset.save()

        dataset.refresh_from_db()

        Upload.objects.create(state="COMPLETE", resource=dataset)

        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse("download", args=(dataset.id,)))
        # headers and status assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get("content-type"), "application/zip")
        self.assertEqual(response.get("content-disposition"), f"attachment; filename={dataset.name}.zip")
        # Inspect content
        zip_content = io.BytesIO(b"".join(response.streaming_content))
        zip = zipfile.ZipFile(zip_content)
        zip_files = zip.namelist()
        self.assertIn(".json", "".join(zip_files))

        link.delete()
        asset.delete()


class OWSApiTestCase(GeoNodeBaseTestSupport):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        create_models(type="dataset")
        # prepare some WMS endpoints
        q = Link.objects.all()
        for lyr in q[:3]:
            lyr.link_type = "OGC:WMS"
            lyr.save()

    def test_ows_api(self):
        url = "/api/ows_endpoints/"
        q = Link.objects.filter(link_type__startswith="OGC:")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content
        if isinstance(content, bytes):
            content = content.decode("UTF-8")
        data = json.loads(content)
        self.assertTrue(len(data["data"]), q.count())


@override_settings(SITEURL="http://localhost:8000")
class TestProxyTags(GeoNodeBaseTestSupport):
    def setUp(self):
        self.maxDiff = None
        self.resource = create_single_dataset("foo_dataset")
        r = RequestFactory()
        self.url = urljoin(settings.SITEURL, reverse("download", args={self.resource.id}))
        r.get(self.url)
        admin = get_user_model().objects.get(username="admin")
        r.user = admin
        self.context = {"request": r}

    def test_tag_original_link_available_with_different_netlock_should_return_true(self):
        actual = original_link_available(self.context, self.resource.resourcebase_ptr_id, "http://url.com/")
        self.assertTrue(actual)

    def test_should_return_false_if_no_files_are_available(self):
        _ = Upload.objects.create(state="RUNNING", resource=self.resource)

        actual = original_link_available(self.context, self.resource.resourcebase_ptr_id, self.url)
        self.assertFalse(actual)

    @patch("geonode.storage.manager.storage_manager.exists", return_value=True)
    def test_should_return_true_if_files_are_available(self, fexists):
        upload = Upload.objects.create(state="RUNNING", resource=self.resource)

        assert upload

        dataset_files = [
            "/tmpe1exb9e9/foo_file.dbf",
            "/tmpe1exb9e9/foo_file.prj",
            "/tmpe1exb9e9/foo_file.shp",
            "/tmpe1exb9e9/foo_file.shx",
        ]

        asset, link = create_asset_and_link(
            self.resource, get_user_model().objects.get(username="admin"), dataset_files, clone_files=False
        )

        self.resource.save()

        self.resource.refresh_from_db()

        actual = original_link_available(self.context, self.resource.resourcebase_ptr_id, self.url)
        self.assertTrue(actual)

        link.delete()
        asset.delete()
