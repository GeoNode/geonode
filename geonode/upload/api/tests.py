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
import json
import shutil
import logging
import tempfile
from io import IOBase
from time import sleep
from unittest import mock
from gisdata import GOOD_DATA, BAD_DATA
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
from geonode.upload.tasks import _update_upload_session_state
from geonode.resource.api.tasks import resouce_service_dispatcher
from geonode.upload.models import Upload, UploadSizeLimit, UploadParallelismLimit
from geonode.upload.tests.utils import (
    GEONODE_USER,
    GEONODE_PASSWD,
    rest_upload_by_path)

LIVE_SERVER_URL = "http://localhost:8001/"
GEOSERVER_URL = ogc_server_settings.LOCATION
GEOSERVER_USER, GEOSERVER_PASSWD = ogc_server_settings.credentials

CURRENT_LOCATION = os.path.abspath(os.path.dirname(__file__))

logger = logging.getLogger(__name__)


@override_settings(
    DEBUG=True,
    ALLOWED_HOSTS=['*'],
    SITEURL=LIVE_SERVER_URL,
    CSRF_COOKIE_SECURE=False,
    CSRF_COOKIE_HTTPONLY=False,
    CORS_ORIGIN_ALLOW_ALL=True,
    SESSION_COOKIE_SECURE=False,
    DEFAULT_MAX_PARALLEL_UPLOADS_PER_USER=5
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

    def test_rest_uploads(self):
        """
        Ensure we can access the Local Server Uploads list.
        """
        # Try to upload a good raster file and check the session IDs
        fname = os.path.join(GOOD_DATA, 'raster', 'relief_san_andres.tif')
        resp, data = rest_upload_by_path(fname, self.client)
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
            self.assertGreaterEqual(upload_data['progress'], 90.0)
            self.assertIsNone(upload_data['resume_url'])
            self.assertIsNone(upload_data['delete_url'])
            self.assertIsNotNone(upload_data['detail_url'])

            self.assertIn('uploadfile_set', upload_data)
            self.assertEqual(len(upload_data['uploadfile_set']), 2)
        else:
            self.assertGreaterEqual(upload_data['progress'], 90.0)
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

    def test_rest_uploads_non_interactive(self):
        """
        Ensure we can access the Local Server Uploads list.
        """
        # Try to upload a good raster file and check the session IDs
        fname = os.path.join(GOOD_DATA, 'raster', 'relief_san_andres.tif')
        resp, data = rest_upload_by_path(fname, self.client, non_interactive=True)
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
            self.assertGreaterEqual(upload_data['progress'], 90.0)
            self.assertIsNone(upload_data['resume_url'])
            self.assertIsNone(upload_data['delete_url'])
            self.assertIsNotNone(upload_data['detail_url'])

            self.assertIn('uploadfile_set', upload_data)
            self.assertEqual(len(upload_data['uploadfile_set']), 2)
        else:
            self.assertGreaterEqual(upload_data['progress'], 90.0)
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

    def test_upload_temp_folder_deleted(self):
        """
        Ensure that temp folders are deleted on deleting a resource
        """
        # Try to upload a good raster file and check the session IDs
        fname = os.path.join(GOOD_DATA, 'raster', 'relief_san_andres.tif')
        resp, data = rest_upload_by_path(fname, self.client)
        self.assertEqual(resp.status_code, 200)
        resource_id = data['url'].split('/')[-1]
        upload = Upload.objects.get(resource_id=resource_id)
        # temp folder is not deleted after successful upload
        self.assertTrue(os.path.exists(upload.upload_dir))

        # delete resource with temp foler
        delete_resource_url = reverse('base-resources-detail', kwargs={'pk': resource_id})
        self.assertTrue(os.path.exists(upload.upload_dir))

        response = self.client.delete(f"{delete_resource_url}/delete")
        self.assertEqual(response.status_code, 200)
        resp_js = json.loads(response.content.decode('utf-8'))
        if resp_js.get("status", "") != "success":
            status_url = resp_js.get("status_url", None)
            execution_id = resp_js.get("execution_id", "")
            self.assertIsNotNone(status_url)
            self.assertIsNotNone(execution_id)
            for _cnt in range(0, 10):
                response = self.client.get(f"{status_url}")
                self.assertEqual(response.status_code, 200)
                resp_js = json.loads(response.content.decode('utf-8'))
                logger.error(f"[{_cnt + 1}] ... {resp_js}")
                if resp_js.get("status", "") == "finished":
                    break
                else:
                    resouce_service_dispatcher.apply((execution_id,))
                    sleep(3.0)
        self.assertEqual(resp_js.get("status", ""), "finished", resp_js)
        self.assertFalse(os.path.exists(upload.upload_dir), resp_js)

    def test_rest_uploads_by_path(self):
        """
        Ensure we can access the Local Server Uploads list.
        """
        # Try to upload a good raster file and check the session IDs
        fname = os.path.join(GOOD_DATA, 'raster', 'relief_san_andres.tif')
        resp, data = rest_upload_by_path(fname, self.client)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data['status'], 'finished')
        self.assertTrue(data['success'])

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
            self.assertGreaterEqual(upload_data['progress'], 90.0)
            self.assertIsNone(upload_data['resume_url'])
            self.assertIsNone(upload_data['delete_url'])
            self.assertIsNotNone(upload_data['detail_url'])

            self.assertIn('uploadfile_set', upload_data)
            self.assertEqual(len(upload_data['uploadfile_set']), 2)
        else:
            self.assertGreaterEqual(upload_data['progress'], 90.0)
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

    def test_rest_uploads_no_crs(self):
        """
        Ensure the upload process turns to `WAITING` status whenever a `CRS` info is missing from the GIS backend.
        """
        # Try to upload a shapefile without a CRS def.
        fname = os.path.join(os.getcwd(), 'geonode/tests/data/san_andres_y_providencia_coastline_no_prj.zip')
        resp, data = rest_upload_by_path(fname, self.client)
        self.assertEqual(resp.status_code, 200)

        url = reverse('uploads-list')
        # Admin
        self.assertTrue(self.client.login(username=GEONODE_USER, password=GEONODE_PASSWD))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5, response.data)
        self.assertEqual(response.data['total'], 1, response.data['total'])
        # Pagination
        self.assertEqual(len(response.data['uploads']), 1)
        self.assertEqual(response.status_code, 200)
        upload_data = response.data['uploads'][0]
        self.assertIsNotNone(upload_data)
        self.assertEqual(upload_data['name'], 'san_andres_y_providencia_coastline_no_prj', upload_data['name'])
        if upload_data['state'] != enumerations.STATE_WAITING:
            for _cnt in range(0, 10):
                response = self.client.get(url, format='json')
                self.assertEqual(response.status_code, 200)
                logger.error(f"[{_cnt + 1}] ... {response.data}")
                upload_data = response.data['uploads'][0]
                self.assertIsNotNone(upload_data)
                self.assertEqual(upload_data['name'], 'san_andres_y_providencia_coastline_no_prj', upload_data['name'])
                if upload_data['state'] == enumerations.STATE_WAITING:
                    break
                else:
                    for _upload in Upload.objects.filter(state=upload_data['state']):
                        _update_upload_session_state.apply((_upload.id,))
                    sleep(3.0)
        self.assertEqual(upload_data['state'], enumerations.STATE_WAITING, upload_data['state'])

        # Try to upload a GeoTIFF without a CRS def.
        fname = os.path.join(os.getcwd(), 'geonode/tests/data/n32_1991_0001_123.tif')
        resp, data = rest_upload_by_path(fname, self.client)
        self.assertEqual(resp.status_code, 200)

        # Admin
        self.assertTrue(self.client.login(username=GEONODE_USER, password=GEONODE_PASSWD))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5, response.data)
        self.assertEqual(response.data['total'], 2, response.data['total'])
        # Pagination
        self.assertEqual(len(response.data['uploads']), 2)
        self.assertEqual(response.status_code, 200)
        upload_data = response.data['uploads'][0]
        self.assertIsNotNone(upload_data)
        self.assertEqual(upload_data['name'], 'n32_1991_0001_123', upload_data['name'])
        if upload_data['state'] != enumerations.STATE_WAITING:
            for _cnt in range(0, 10):
                response = self.client.get(url, format='json')
                self.assertEqual(response.status_code, 200)
                logger.error(f"[{_cnt + 1}] ... {response.data}")
                upload_data = response.data['uploads'][0]
                self.assertIsNotNone(upload_data)
                self.assertEqual(upload_data['name'], 'n32_1991_0001_123', upload_data['name'])
                if upload_data['state'] == enumerations.STATE_WAITING:
                    break
                else:
                    for _upload in Upload.objects.filter(state=upload_data['state']):
                        _update_upload_session_state.apply((_upload.id,))
                    sleep(3.0)
        self.assertEqual(upload_data['state'], enumerations.STATE_WAITING, upload_data['state'])

    def test_emulate_upload_through_rest_apis(self):
        """
        Emulating Upload via REST APIs with several datasets.
        """
        # Try to upload a bad ESRI shapefile with no CRS available
        fname = os.path.join(BAD_DATA, 'points_epsg2249_no_prj.shp')
        resp, data = rest_upload_by_path(fname, self.client)
        self.assertEqual(resp.status_code, 200)

        # Try to upload a good raster file and check the session IDs
        fname = os.path.join(GOOD_DATA, 'raster', 'relief_san_andres.tif')
        resp, data = rest_upload_by_path(fname, self.client)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data['status'], 'finished')
        self.assertTrue(data['success'])

        # Try to upload a good ESRI shapefile and check the session IDs
        fname = os.path.join(GOOD_DATA, 'vector', 'san_andres_y_providencia_coastline.shp')
        resp, data = rest_upload_by_path(fname, self.client)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data['status'], 'finished')
        self.assertTrue(data['success'])

        def assert_processed_or_failed(total_uploads, upload_index, dataset_name, state):
            url = reverse('uploads-list')
            # Admin
            self.assertTrue(self.client.login(username=GEONODE_USER, password=GEONODE_PASSWD))
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data), 5, response.data)
            self.assertEqual(response.data['total'], total_uploads, response.data['total'])
            # Pagination
            self.assertEqual(len(response.data['uploads']), total_uploads)
            self.assertEqual(response.status_code, 200)

            upload_data = response.data['uploads'][upload_index]
            self.assertIsNotNone(upload_data)
            self.assertEqual(upload_data['name'], dataset_name, upload_data['name'])
            if upload_data['state'] != state:
                for _cnt in range(0, 10):
                    response = self.client.get(url, format='json')
                    self.assertEqual(response.status_code, 200)
                    logger.error(f"[{_cnt + 1}] ... {response.data}")
                    upload_data = response.data['uploads'][upload_index]
                    self.assertIsNotNone(upload_data)
                    self.assertEqual(upload_data['name'], dataset_name, upload_data['name'])
                    if upload_data['state'] == state:
                        break
                    else:
                        for _upload in Upload.objects.filter(state=upload_data['state']):
                            _update_upload_session_state.apply((_upload.id,))
                        sleep(3.0)
            self.assertEqual(upload_data['state'], state, upload_data['state'])

        # Vector
        assert_processed_or_failed(3, 0, 'san_andres_y_providencia_coastline', enumerations.STATE_PROCESSED)

        # Raster
        assert_processed_or_failed(3, 1, 'relief_san_andres', enumerations.STATE_PROCESSED)

        # Unsupported
        assert_processed_or_failed(3, 2, 'points_epsg2249_no_prj', enumerations.STATE_WAITING)

    @mock.patch("geonode.upload.uploadhandler.SimpleUploadedFile")
    def test_rest_uploads_with_size_limit(self, mocked_uploaded_file):
        """
        Try to upload a file larger than allowed by ``dataset_upload_size``
        but not larger than ``file_upload_handler`` max_size.
        """
        expected_error = {
            "success": False,
            "errors": ["Total upload size exceeds 1\xa0byte. Please try again with smaller files."],
            "code": "total_upload_size_exceeded"
        }
        upload_size_limit_obj, created = UploadSizeLimit.objects.get_or_create(
            slug="dataset_upload_size",
            defaults={
                "description": "The sum of sizes for the files of a dataset upload.",
                "max_size": 1,
            }
        )
        upload_size_limit_obj.max_size = 1
        upload_size_limit_obj.save()

        # Try to upload and verify if it passed only by the form size validation
        fname = os.path.join(GOOD_DATA, 'raster', 'relief_san_andres.tif')

        max_size_path = "geonode.upload.uploadhandler.SizeRestrictedFileUploadHandler._get_max_size"
        with mock.patch(max_size_path, new_callable=mock.PropertyMock) as max_size_mock:
            max_size_mock.return_value = lambda x: 209715200

            resp, data = rest_upload_by_path(fname, self.client)
            self.assertEqual(resp.status_code, 400)
            self.assertDictEqual(expected_error, data)
            mocked_uploaded_file.assert_not_called()

    @mock.patch("geonode.upload.uploadhandler.SimpleUploadedFile")
    def test_rest_uploads_with_size_limit_before_upload(self, mocked_uploaded_file):
        """
        Try to upload a file larger than allowed by ``file_upload_handler``.
        """
        expected_error = {
            "success": False,
            "errors": ["Total upload size exceeds 1\xa0byte. Please try again with smaller files."],
            "code": "total_upload_size_exceeded"
        }
        upload_size_limit_obj, created = UploadSizeLimit.objects.get_or_create(
            slug="dataset_upload_size",
            defaults={
                "description": "The sum of sizes for the files of a dataset upload.",
                "max_size": 1,
            }
        )
        upload_size_limit_obj.max_size = 1
        upload_size_limit_obj.save()

        # Try to upload and verify if it passed by both size validations
        fname = os.path.join(GOOD_DATA, 'raster', 'relief_san_andres.tif')
        max_size_path = "geonode.upload.uploadhandler.SizeRestrictedFileUploadHandler._get_max_size"
        with mock.patch(max_size_path, new_callable=mock.PropertyMock) as max_size_mock:
            max_size_mock.return_value = lambda x: 1

            resp, data = rest_upload_by_path(fname, self.client)
            # Assertions
            self.assertEqual(resp.status_code, 400)
            self.assertDictEqual(expected_error, data)
            mocked_uploaded_file.assert_called_with(
                name='relief_san_andres.tif',
                content=b'',
                content_type='image/tiff'
            )

    @mock.patch("geonode.upload.uploadhandler.SimpleUploadedFile")
    def test_rest_uploads_with_parallelism_limit(self, mocked_uploaded_file):
        """
        Try to upload a file when there are many others being handled.
        """

        expected_error = {
            "success": False,
            "errors": ["The number of active parallel uploads exceeds 100. Wait for the pending ones to finish."],
            "code": "upload_parallelism_limit_exceeded"
        }
        # Try to upload and verify if it passed only by the form size validation
        fname = os.path.join(GOOD_DATA, 'raster', 'relief_san_andres.tif')

        _get_parallel_uploads_count_path = "geonode.upload.forms.UploadLimitValidator._get_parallel_uploads_count"
        with mock.patch(_get_parallel_uploads_count_path, new_callable=mock.PropertyMock) as mocked_get_parallel_uploads_count:
            mocked_get_parallel_uploads_count.return_value = lambda: 200

            resp, data = rest_upload_by_path(fname, self.client)
            self.assertEqual(resp.status_code, 400)

            mocked_uploaded_file.assert_not_called()
            self.assertDictEqual(expected_error, data)


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
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.wsgi_request.user, self.admin)

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
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.wsgi_request.user, self.admin)

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
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.wsgi_request.user, self.admin)

    def test_delete_size_limit_anonymous_user(self):
        url = reverse('upload-size-limits-detail', args=('some-other-size-limit',))

        # List as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.delete(url)

        # Assertions
        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.wsgi_request.user.is_anonymous)


class UploadParallelismLimitTests(APITestCase):
    fixtures = [
        'group_test_data.json',
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = get_user_model().objects.get(username="admin")
        cls.norman_user = get_user_model().objects.get(username="norman")
        cls.test_user = get_user_model().objects.get(username="test_user")
        try:
            cls.default_parallelism_limit = UploadParallelismLimit.objects.get(slug="default_max_parallel_uploads")
        except UploadParallelismLimit.DoesNotExist:
            cls.default_parallelism_limit = UploadParallelismLimit.objects.create_default_limit()

    def test_list_parallelism_limits_admin_user(self):
        url = reverse('upload-parallelism-limits-list')

        # List as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.admin)
        # Response Content
        parallelism_limits = [
            (parallelism_limit['slug'], parallelism_limit['max_number'])
            for parallelism_limit in response.json()['upload-parallelism-limits']
        ]
        expected_parallelism_limits = [
            (self.default_parallelism_limit.slug, self.default_parallelism_limit.max_number),
        ]
        for parallelism_limit in expected_parallelism_limits:
            self.assertIn(parallelism_limit, parallelism_limits)

    def test_list_parallelism_limits_anonymous_user(self):
        url = reverse('upload-parallelism-limits-list')

        # List as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_anonymous)
        # Response Content
        parallelism_limits = [
            (parallelism_limit['slug'], parallelism_limit['max_number'])
            for parallelism_limit in response.json()['upload-parallelism-limits']
        ]
        expected_parallelism_limits = [
            (self.default_parallelism_limit.slug, self.default_parallelism_limit.max_number),
        ]
        for parallelism_limit in expected_parallelism_limits:
            self.assertIn(parallelism_limit, parallelism_limits)

    def test_retrieve_parallelism_limit_admin_user(self):
        url = reverse('upload-parallelism-limits-detail', args=(self.default_parallelism_limit.slug,))

        # Retrieve as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.admin)
        # Response Content
        parallelism_limit = response.json()['upload-parallelism-limit']
        self.assertEqual(parallelism_limit['slug'], self.default_parallelism_limit.slug)
        self.assertEqual(parallelism_limit['max_number'], self.default_parallelism_limit.max_number)

    def test_retrieve_parallelism_limit_norman_user(self):
        url = reverse('upload-parallelism-limits-detail', args=(self.default_parallelism_limit.slug,))

        # Retrieve as a norman user
        self.client.force_authenticate(user=self.norman_user)
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.norman_user)
        # Response Content
        parallelism_limit = response.json()['upload-parallelism-limit']
        self.assertEqual(parallelism_limit['slug'], self.default_parallelism_limit.slug)
        self.assertEqual(parallelism_limit['max_number'], self.default_parallelism_limit.max_number)

    def test_patch_parallelism_limit_admin_user(self):
        url = reverse('upload-parallelism-limits-detail', args=(self.default_parallelism_limit.slug,))

        # Patch as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(url, data={"max_number": 3})

        # Assertions
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.wsgi_request.user, self.admin)

    def test_patch_parallelism_limit_norman_user(self):
        url = reverse('upload-parallelism-limits-detail', args=(self.default_parallelism_limit.slug,))

        # Patch as a norman user
        self.client.force_authenticate(user=None)
        response = self.client.patch(url, data={"max_number": 4})

        # Assertions
        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.wsgi_request.user.is_anonymous)

    def test_patch_parallelism_limit_anonymous_user(self):
        url = reverse('upload-parallelism-limits-detail', args=(self.default_parallelism_limit.slug,))

        # Patch as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.patch(url, data={"max_number": 6})

        # Assertions
        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.wsgi_request.user.is_anonymous)

    def test_put_parallelism_limit_admin_user(self):
        url = reverse('upload-parallelism-limits-detail', args=(self.default_parallelism_limit.slug,))

        # Put as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(url, data={"slug": self.default_parallelism_limit.slug, "max_number": 7})

        # Assertions
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.wsgi_request.user, self.admin)

    def test_put_parallelism_limit_anonymous_user(self):
        url = reverse('upload-parallelism-limits-detail', args=(self.default_parallelism_limit.slug,))

        # Put as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.put(url, data={"slug": self.default_parallelism_limit.slug, "max_number": 8})

        # Assertions
        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.wsgi_request.user.is_anonymous)

    def test_post_parallelism_limit_admin_user(self):
        url = reverse('upload-parallelism-limits-list')

        # Post as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data={"slug": "some-parallelism-limit", "max_number": 9})

        # Assertions
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.wsgi_request.user, self.admin)
        # Response Content
        parallelism_limit = response.json()['upload-parallelism-limit']
        self.assertEqual(parallelism_limit['slug'], 'some-parallelism-limit')
        self.assertEqual(parallelism_limit['max_number'], 9)

    def test_post_parallelism_limit_anonymous_user(self):
        url = reverse('upload-parallelism-limits-list')

        # Post as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.post(url, data={"slug": 'some-parallelism-limit', "max_number": 8})

        # Assertions
        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.wsgi_request.user.is_anonymous)

    def test_delete_parallelism_limit_admin_user(self):
        UploadParallelismLimit.objects.create(slug="test-parallelism-limit", max_number=123,)
        url = reverse('upload-parallelism-limits-detail', args=('test-parallelism-limit',))

        # Delete as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(url)

        # Assertions
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.wsgi_request.user, self.admin)

    def test_delete_parallelism_limit_admin_user_protected(self):
        url = reverse('upload-parallelism-limits-detail', args=(self.default_parallelism_limit.slug,))

        # Delete as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(url)

        # Assertions
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.wsgi_request.user, self.admin)

    def test_delete_parallelism_limit_anonymous_user(self):
        UploadParallelismLimit.objects.create(slug="test-parallelism-limit", max_number=123,)
        url = reverse('upload-parallelism-limits-detail', args=('test-parallelism-limit',))

        # Delete as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.delete(url)

        # Assertions
        self.assertEqual(response.status_code, 403)
        self.assertTrue(response.wsgi_request.user.is_anonymous)
