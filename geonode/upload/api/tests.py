#########################################################################
#
# Copyright (C) 2021 OSGeo
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
import os
import shutil
import logging
import tempfile
from unittest import mock

from io import IOBase
from gisdata import GOOD_DATA
from urllib.request import urljoin

from django.conf import settings

from django.urls import reverse
from django.contrib.auth import authenticate, get_user_model
from django.test.utils import override_settings

from requests_toolbelt.multipart.encoder import MultipartEncoder

from rest_framework.test import APITestCase

from seleniumrequests import Firefox
# from selenium.common import exceptions
# from selenium.webdriver.common.by import By
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

from webdriver_manager.firefox import GeckoDriverManager

from geonode.base import enumerations
from geonode.tests.base import GeoNodeLiveTestSupport
from geonode.geoserver.helpers import ogc_server_settings
from geonode.upload.models import UploadSizeLimit

GEONODE_USER = 'admin'
GEONODE_PASSWD = 'admin'
LIVE_SERVER_URL = "http://localhost:8001/"
GEOSERVER_URL = ogc_server_settings.LOCATION
GEOSERVER_USER, GEOSERVER_PASSWD = ogc_server_settings.credentials

CURRENT_LOCATION = os.path.abspath(os.path.dirname(__file__))

logger = logging.getLogger(__name__)


@override_settings(
    DEBUG=True,
    ALLOWED_HOSTS=['*'],
    CSRF_COOKIE_SECURE=False,
    CSRF_COOKIE_HTTPONLY=False,
    CORS_ORIGIN_ALLOW_ALL=True,
    SESSION_COOKIE_SECURE=False,
    SITEURL=LIVE_SERVER_URL,
)
class UploadApiTests(GeoNodeLiveTestSupport, APITestCase):

    port = 0

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        try:
            """ Instantiate selenium driver instance """
            binary = FirefoxBinary('/usr/bin/firefox')
            opts = FirefoxOptions()
            opts.add_argument("--headless")
            executable_path = GeckoDriverManager().install()
            cls.selenium = Firefox(
                firefox_binary=binary,
                firefox_options=opts,
                executable_path=executable_path)
            cls.selenium.implicitly_wait(10)
        except Exception as e:
            logger.error(e)

    @classmethod
    def tearDownClass(cls):
        """ Quit selenium driver instance """
        try:
            cls.selenium.quit()
        except Exception as e:
            logger.debug(e)
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.temp_folder = tempfile.mkdtemp(dir=CURRENT_LOCATION)
        self.session_id = None
        self.csrf_token = None

    def tearDown(self):
        shutil.rmtree(self.temp_folder, ignore_errors=True)
        return super().tearDown()

    def set_session_cookies(self, url=None):
        # selenium will set cookie domain based on current page domain
        self.selenium.get(url or f'{self.live_server_url}/')
        self.csrf_token = self.selenium.get_cookie('csrftoken')['value']
        self.session_id = self.selenium.get_cookie(settings.SESSION_COOKIE_NAME)['value']
        self.selenium.add_cookie(
            {'name': settings.SESSION_COOKIE_NAME, 'value': self.session_id, 'secure': False, 'path': '/'})
        self.selenium.add_cookie(
            {'name': 'csrftoken', 'value': self.csrf_token, 'secure': False, 'path': '/'})

    def click_button(self, label):
        selector = f"//button[contains(., '{label}')]"
        self.selenium.find_element_by_xpath(selector).click()

    def do_login(self, username=GEONODE_USER, password=GEONODE_PASSWD):
        """ Method to login the GeoNode site"""
        assert authenticate(username=username, password=password)
        self.assertTrue(self.client.login(username=username, password=password))  # Native django test client

        url = urljoin(
            settings.SITEURL,
            f"{reverse('account_login')}?next=/layers"
        )
        self.set_session_cookies(url)
        self.selenium.save_screenshot(os.path.join(self.temp_folder, 'login.png'))

        title = self.selenium.title
        current_url = self.selenium.current_url
        logger.debug(f" ---- title: {title} / current_url: {current_url}")

        username_input = self.selenium.find_element_by_xpath('//input[@id="id_login"][@type="text"]')
        username_input.send_keys(username)
        password_input = self.selenium.find_element_by_xpath('//input[@id="id_password"][@type="password"]')
        password_input.send_keys(password)

        self.selenium.save_screenshot(os.path.join(self.temp_folder, 'login-set_fields.png'))
        self.click_button("Sign In")
        self.selenium.save_screenshot(os.path.join(self.temp_folder, 'login-sign_in.png'))

        title = self.selenium.title
        current_url = self.selenium.current_url
        logger.debug(f" ---- title: {title} / current_url: {current_url}")

        # Wait until the response is received
        WebDriverWait(self.selenium, 10).until(
            EC.title_contains("Explore Layers")
        )
        self.set_session_cookies(url)

    def do_logout(self):
        url = urljoin(
            settings.SITEURL,
            f"{reverse('account_logout')}"
        )
        self.selenium.get(url)
        self.click_button("Log out")

    def do_upload_step(self, step=None):
        step = urljoin(
            settings.SITEURL,
            reverse('data_upload', args=[step] if step else [])
        )
        return step

    def as_superuser(func):
        def wrapper(self, *args, **kwargs):
            self.do_login()
            func(self, *args, **kwargs)
            self.do_logout()
        return wrapper

    def live_upload_file(self, _file):
        """ function that uploads a file, or a collection of files, to
        the GeoNode"""
        spatial_files = ("dbf_file", "shx_file", "prj_file")
        base, ext = os.path.splitext(_file)
        params = {
            # make public since wms client doesn't do authentication
            'csrfmiddlewaretoken': self.csrf_token,
            'permissions': '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            'time': 'false',
            'charset': 'UTF-8'
        }
        cookies = {
            settings.SESSION_COOKIE_NAME: self.session_id,
            'csrftoken': self.csrf_token
        }
        headers = {
            'X-CSRFToken': self.csrf_token,
            'X-Requested-With': 'XMLHttpRequest',
            'Set-Cookie': f'csrftoken={self.csrf_token}; sessionid={self.session_id}'
        }
        url = self.do_upload_step()
        logger.debug(f" ---- UPLOAD URL: {url} / cookies: {cookies} / headers: {headers}")

        # deal with shapefiles
        if ext.lower() == '.shp':
            for spatial_file in spatial_files:
                ext, _ = spatial_file.split('_')
                file_path = f"{base}.{ext}"
                # sometimes a shapefile is missing an extra file,
                # allow for that
                if os.path.exists(file_path):
                    params[spatial_file] = open(file_path, 'rb')

        with open(_file, 'rb') as base_file:
            params['base_file'] = base_file
            for name, value in params.items():
                if isinstance(value, IOBase):
                    params[name] = (os.path.basename(value.name), value)

            # refresh to exchange cookies with the server.
            self.selenium.refresh()
            self.selenium.get(url)
            self.selenium.save_screenshot(os.path.join(self.temp_folder, 'upload-page.png'))
            logger.debug(f" ------------ UPLOAD FORM: {params}")
            encoder = MultipartEncoder(fields=params)
            headers['Content-Type'] = encoder.content_type
            response = self.selenium.request(
                'POST',
                url,
                data=encoder,
                headers=headers)

        # Closes the files
        for spatial_file in spatial_files:
            if isinstance(params.get(spatial_file), IOBase):
                params[spatial_file].close()

        try:
            logger.error(f" -- response: {response.status_code} / {response.json()}")
            return response, response.json()
        except ValueError:
            logger.exception(
                ValueError(
                    f"probably not json, status {response.status_code} / {response.content}"))
            return response, response.content

    def rest_upload_file(self, _file, username=GEONODE_USER, password=GEONODE_PASSWD):
        """ function that uploads a file, or a collection of files, to
        the GeoNode"""
        assert authenticate(username=username, password=password)
        self.assertTrue(self.client.login(username=username, password=password))
        spatial_files = ("dbf_file", "shx_file", "prj_file")
        base, ext = os.path.splitext(_file)
        params = {
            # make public since wms client doesn't do authentication
            'permissions': '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            'time': 'false',
            'charset': 'UTF-8'
        }

        # deal with shapefiles
        if ext.lower() == '.shp':
            for spatial_file in spatial_files:
                ext, _ = spatial_file.split('_')
                file_path = f"{base}.{ext}"
                # sometimes a shapefile is missing an extra file,
                # allow for that
                if os.path.exists(file_path):
                    params[spatial_file] = open(file_path, 'rb')

        with open(_file, 'rb') as base_file:
            params['base_file'] = base_file
            for name, value in params.items():
                if isinstance(value, IOBase):
                    params[name] = (os.path.basename(value.name), value)
            url = urljoin(
                f"{reverse('uploads-list')}/",
                'upload/')
            logger.error(f" ---- UPLOAD URL: {url}")
            response = self.client.post(url, data=params)

        # Closes the files
        for spatial_file in spatial_files:
            if isinstance(params.get(spatial_file), IOBase):
                params[spatial_file].close()

        try:
            logger.error(f" -- response: {response.status_code} / {response.json()}")
            return response, response.json()
        except (ValueError, TypeError):
            logger.exception(
                ValueError(
                    f"probably not json, status {response.status_code} / {response.content}"))
            return response, response.content

    # AF: Intermittent failures on CircleCI
    # @as_superuser
    # def test_live_login(self):
    #     """
    #     Try to login to Live Server using the integrated "selenium" framework
    #     """
    #     pass

    # AF: Intermittent failures on CircleCI
    # @as_superuser
    # def test_live_uploads(self):
    #     """
    #     Ensure we can access the Live Server Uploads list.
    #     """
    #     # Try to upload a good raster file and check the session IDs
    #     fname = os.path.join(GOOD_DATA, 'raster', 'relief_san_andres.tif')
    #     resp, data = self.live_upload_file(fname)
    #     self.assertEqual(resp.status_code, 200)
    #     self.assertTrue(data['success'])
    #     self.assertIn('redirect_to', data)
    #     headers = {
    #         'X-CSRFToken': self.csrf_token,
    #         'X-Requested-With': 'XMLHttpRequest',
    #         'Cookie': f'csrftoken={self.csrf_token}; sessionid={self.session_id}'
    #     }
    #     url = urljoin(
    #         settings.SITEURL,
    #         f"{reverse('uploads-list')}.json")
    #     response = self.selenium.request('GET', url, headers=headers)
    #     self.assertEqual(response.status_code, 200)
    #     response_data = response.json()
    #     self.assertEqual(len(response_data), 5)
    #     total_uploads = response_data['total']
    #     self.assertGreaterEqual(total_uploads, 1)
    #     # Pagination
    #     self.assertEqual(len(response_data['uploads']), 10)
    #     logger.debug(response_data)
    #     upload_data = response_data['uploads'][0]
    #     self.assertIsNotNone(upload_data)
    #     self.assertIn('relief_san_andres', upload_data['name'])
    #     self.assertEqual(upload_data['state'], enumerations.STATE_PENDING)
    #     self.assertEqual(upload_data['progress'], 33.0)
    #     self.assertIsNone(upload_data['detail_url'])
    #     self.assertIsNone(upload_data['resume_url'])
    #     self.assertIsNotNone(upload_data['delete_url'])
    #     delete_url = urljoin(
    #         settings.SITEURL,
    #         f"{upload_data['delete_url']}"
    #     )
    #     url = urljoin(
    #         settings.SITEURL,
    #         f"{reverse('data_upload')}?id={upload_data['import_id']}"
    #     )
    #     response = self.selenium.request('GET', url, headers=headers)
    #     self.assertEqual(response.status_code, 200)
    #     url = urljoin(
    #         settings.SITEURL,
    #         f"{self.do_upload_step('final')}?id={response_data['uploads'][0]['import_id']}")
    #     response = self.selenium.request('GET', url, headers=headers)
    #     self.assertEqual(response.status_code, 200)
    #     upload_data = response_data['uploads'][0]
    #     for _cnt in range(1, 10):
    #         logger.error(f"[{_cnt}] Wait a bit until GeoNode finalizes the Dataset configuration...")
    #         if upload_data['state'] == enumerations.STATE_PROCESSED:
    #             break
    #         time.sleep(10.0)
    #     if upload_data['state'] == enumerations.STATE_PROCESSED:
    #         self.assertGreaterEqual(upload_data['progress'], 80.0)
    #         self.assertIsNotNone(upload_data['detail_url'])
    #         self.assertIsNone(upload_data['resume_url'])
    #         self.assertIsNone(upload_data['delete_url'])
    #     elif upload_data['state'] == enumerations.STATE_PENDING:
    #         self.assertGreaterEqual(upload_data['progress'], 33.0)
    #         self.assertIsNone(upload_data['detail_url'])
    #         self.assertIsNone(upload_data['resume_url'])
    #         self.assertIsNotNone(upload_data['delete_url'])
    #     response = self.selenium.request('GET', delete_url, headers=headers)
    #     self.assertEqual(response.status_code, 200)
    #     url = urljoin(
    #         settings.SITEURL,
    #         f"{reverse('uploads-list')}.json"
    #     )
    #     response = self.selenium.request('GET', url, headers=headers)
    #     self.assertEqual(response.status_code, 200)
    #     response_data = response.json()
    #     self.assertEqual(len(response_data), 5)
    #     self.assertEqual(response_data['total'], total_uploads - 1)
    #     # Pagination
    #     self.assertEqual(len(response_data['uploads']), 10)
    #     logger.debug(response_data)

    def test_rest_uploads(self):
        """
        Ensure we can access the Local Server Uploads list.
        """
        # Try to upload a good raster file and check the session IDs
        fname = os.path.join(GOOD_DATA, 'raster', 'relief_san_andres.tif')
        resp, data = self.rest_upload_file(fname)
        self.assertEqual(resp.status_code, 200)

        url = reverse('uploads-list')
        # Anonymous
        self.client.logout()
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 0)
        # Pagination
        self.assertEqual(len(response.data['uploads']), 0)
        logger.debug(response.data)

        # Admin
        self.assertTrue(self.client.login(username=GEONODE_USER, password=GEONODE_PASSWD))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 1)
        # Pagination
        self.assertEqual(len(response.data['uploads']), 1)
        logger.debug(response.data)
        upload_data = response.data['uploads'][0]
        self.assertIsNotNone(upload_data)
        self.assertEqual(upload_data['name'], 'relief_san_andres')

        if upload_data['state'] != enumerations.STATE_PROCESSED:
            self.assertEqual(upload_data['progress'], 100.0)
            self.assertIsNone(upload_data['resume_url'])
            self.assertIsNone(upload_data['delete_url'])
            self.assertIsNotNone(upload_data['detail_url'])

            self.assertIn('uploadfile_set', upload_data)
            self.assertEqual(len(upload_data['uploadfile_set']), 2)
        else:
            self.assertEqual(upload_data['progress'], 100.0)
            self.assertIsNone(upload_data['resume_url'])
            self.assertIsNone(upload_data['delete_url'])
            self.assertIsNotNone(upload_data['detail_url'])

        self.assertNotIn('resource', upload_data)
        self.assertNotIn('session', upload_data)

        url = reverse('uploads-detail', kwargs={'pk': upload_data['id']})
        response = self.client.get(f"{url}?full=true", format='json')
        self.assertEqual(response.status_code, 200)
        upload_data = response.data['upload']
        self.assertIsNotNone(upload_data)
        self.assertIn('resource', upload_data)
        self.assertIn('ptype', upload_data['resource'])
        self.assertIn('ows_url', upload_data['resource'])
        self.assertIn('subtype', upload_data['resource'])

        self.assertIn('session', upload_data)

        self.assertIn('uploadfile_set', upload_data)
        self.assertGreaterEqual(len(upload_data['uploadfile_set']), 1)

        self.assertNotIn('upload_dir', upload_data)

        if upload_data['delete_url'] is not None:
            response = self.client.get(upload_data['delete_url'], format='json')
            self.assertEqual(response.status_code, 200)

            response = self.client.get(reverse('uploads-list'), format='json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data), 5)
            self.assertEqual(response.data['total'], 0)
            # Pagination
            self.assertEqual(len(response.data['uploads']), 0)
            logger.debug(response.data)

    @mock.patch("geonode.upload.forms.forms.ValidationError")
    @mock.patch("geonode.upload.uploadhandler.SimpleUploadedFile")
    def test_rest_uploads_with_size_limit(self, mocked_uploaded_file, mocked_validation_error):
        """
        Try to upload a file larger than allowed by ``total_upload_size_sum``
        but not larger than ``file_upload_handler`` max_size.
        """

        upload_size_limit_obj, created = UploadSizeLimit.objects.get_or_create(
            slug="total_upload_size_sum",
            defaults={
                "description": "The sum of sizes for the files of a dataset upload.",
                "max_size": 1,
            }
        )
        upload_size_limit_obj.max_size = 1
        upload_size_limit_obj.save()

        handler_upload_size_limit_obj, created = UploadSizeLimit.objects.get_or_create(
            slug="file_upload_handler",
            defaults={
                "description": (
                    "Request total size, validated before the upload process. "
                    'This should be greater than "total_upload_size_sum".'
                ),
                "max_size": 209715200,
            },
        )
        handler_upload_size_limit_obj.max_size = 209715200  # Greater than 173708 bytes (test request size)
        handler_upload_size_limit_obj.save()

        # Try to upload and verify if it passed only by the form size validation
        fname = os.path.join(GOOD_DATA, 'raster', 'relief_san_andres.tif')
        resp, data = self.rest_upload_file(fname)
        self.assertEqual(resp.status_code, 400)
        expected_error = 'Total upload size exceeds 1\xa0byte. Please try again with smaller files.'
        mocked_validation_error.assert_called_once_with(expected_error)
        mocked_uploaded_file.assert_not_called()

    @mock.patch("geonode.upload.forms.forms.ValidationError")
    @mock.patch("geonode.upload.uploadhandler.SimpleUploadedFile")
    def test_rest_uploads_with_size_limit_before_upload(self, mocked_uploaded_file, mocked_validation_error):
        """
        Try to upload a file larger than allowed by ``file_upload_handler``.
        """

        upload_size_limit_obj, created = UploadSizeLimit.objects.get_or_create(
            slug="total_upload_size_sum",
            defaults={
                "description": "The sum of sizes for the files of a dataset upload.",
                "max_size": 1,
            }
        )
        upload_size_limit_obj.max_size = 1
        upload_size_limit_obj.save()

        handler_upload_size_limit_obj, created = UploadSizeLimit.objects.get_or_create(
            slug="file_upload_handler",
            defaults={
                "description": (
                    "Request total size, validated before the upload process. "
                    'This should be greater than "total_upload_size_sum".'
                ),
                "max_size": 2,
            },
        )
        handler_upload_size_limit_obj.max_size = 2
        handler_upload_size_limit_obj.save()

        # Try to upload and verify if it passed by both size validations
        fname = os.path.join(GOOD_DATA, 'raster', 'relief_san_andres.tif')
        resp, data = self.rest_upload_file(fname)
        # Assertions
        self.assertEqual(resp.status_code, 400)
        expected_error = 'Total upload size exceeds 1\xa0byte. Please try again with smaller files.'
        mocked_validation_error.assert_called_once_with(expected_error)
        mocked_uploaded_file.assert_called_with(
            name='relief_san_andres.tif',
            content=b'',
            content_type='image/tiff'
        )


class UploadSizeLimitTests(APITestCase):
    fixtures = [
        'group_test_data.json',
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = get_user_model().objects.get(username="admin")
        UploadSizeLimit.objects.create(
            slug="some-size-limit",
            description="some description",
            max_size=104857600,  # 100 MB
        )
        UploadSizeLimit.objects.create(
            slug="some-other-size-limit",
            description="some other description",
            max_size=52428800,  # 50 MB
        )

    def test_list_size_limits_admin_user(self):
        url = reverse('upload-size-limits-list')

        # List as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.admin)
        # Response Content
        size_limits = [
            (size_limit['slug'], size_limit['max_size'], size_limit['max_size_label'])
            for size_limit in response.json()['upload-size-limits']
        ]
        expected_size_limits = [
            ('some-size-limit', 104857600, '100.0\xa0MB'),
            ('some-other-size-limit', 52428800, '50.0\xa0MB'),
        ]
        for size_limit in expected_size_limits:
            self.assertIn(size_limit, size_limits)

    def test_list_size_limits_anonymous_user(self):
        url = reverse('upload-size-limits-list')

        # List as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_anonymous)
        # Response Content
        size_limits = [
            (size_limit['slug'], size_limit['max_size'], size_limit['max_size_label'])
            for size_limit in response.json()['upload-size-limits']
        ]
        expected_size_limits = [
            ('some-size-limit', 104857600, '100.0\xa0MB'),
            ('some-other-size-limit', 52428800, '50.0\xa0MB'),
        ]
        for size_limit in expected_size_limits:
            self.assertIn(size_limit, size_limits)

    def test_retrieve_size_limit_admin_user(self):
        url = reverse('upload-size-limits-detail', args=('some-size-limit',))

        # List as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.admin)
        # Response Content
        size_limit = response.json()['upload-size-limit']
        self.assertEqual(size_limit['slug'], 'some-size-limit')
        self.assertEqual(size_limit['max_size'], 104857600)
        self.assertEqual(size_limit['max_size_label'], '100.0\xa0MB')

    def test_retrieve_size_limit_anonymous_user(self):
        url = reverse('upload-size-limits-detail', args=('some-size-limit',))

        # List as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_anonymous)
        # Response Content
        size_limit = response.json()['upload-size-limit']
        self.assertEqual(size_limit['slug'], 'some-size-limit')
        self.assertEqual(size_limit['max_size'], 104857600)
        self.assertEqual(size_limit['max_size_label'], '100.0\xa0MB')

    def test_patch_size_limit_admin_user(self):
        url = reverse('upload-size-limits-detail', args=('some-size-limit',))

        # List as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(url, data={"max_size": 5242880})

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.admin)
        # Response Content
        size_limit = response.json()['upload-size-limit']
        self.assertEqual(size_limit['slug'], 'some-size-limit')
        self.assertEqual(size_limit['max_size'], 5242880)
        self.assertEqual(size_limit['max_size_label'], '5.0\xa0MB')

    def test_patch_size_limit_anonymous_user(self):
        url = reverse('upload-size-limits-detail', args=('some-size-limit',))

        # List as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.patch(url, data={"max_size": 2621440})

        # Assertions
        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.wsgi_request.user.is_anonymous)

    def test_put_size_limit_admin_user(self):
        url = reverse('upload-size-limits-detail', args=('some-size-limit',))

        # List as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(url, data={"slug": "some-size-limit", "max_size": 5242880})

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.admin)
        # Response Content
        size_limit = response.json()['upload-size-limit']
        self.assertEqual(size_limit['slug'], 'some-size-limit')
        self.assertEqual(size_limit['max_size'], 5242880)
        self.assertEqual(size_limit['max_size_label'], '5.0\xa0MB')

    def test_put_size_limit_anonymous_user(self):
        url = reverse('upload-size-limits-detail', args=('some-size-limit',))

        # List as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.put(url, data={"slug": "some-size-limit", "max_size": 2621440})

        # Assertions
        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.wsgi_request.user.is_anonymous)

    def test_post_size_limit_admin_user(self):
        url = reverse('upload-size-limits-list')

        # List as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data={"slug": "some-new-slug", "max_size": 5242880})

        # Assertions
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.wsgi_request.user, self.admin)
        # Response Content
        size_limit = response.json()['upload-size-limit']
        self.assertEqual(size_limit['slug'], 'some-new-slug')
        self.assertEqual(size_limit['max_size'], 5242880)
        self.assertEqual(size_limit['max_size_label'], '5.0\xa0MB')

    def test_post_size_limit_anonymous_user(self):
        url = reverse('upload-size-limits-list')

        # List as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.post(url, data={"slug": "other-new-slug", "max_size": 2621440})

        # Assertions
        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.wsgi_request.user.is_anonymous)

    def test_delete_size_limit_admin_user(self):
        url = reverse('upload-size-limits-detail', args=('some-size-limit',))

        # List as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(url)

        # Assertions
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.wsgi_request.user, self.admin)

    def test_delete_size_limit_anonymous_user(self):
        url = reverse('upload-size-limits-detail', args=('some-other-size-limit',))

        # List as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.delete(url)

        # Assertions
        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.wsgi_request.user.is_anonymous)
