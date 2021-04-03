# -*- coding: utf-8 -*-
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
import logging

from io import IOBase
from gisdata import GOOD_DATA
from urllib.request import urljoin

from django.conf import settings

from django.urls import reverse
from django.test.utils import override_settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from rest_framework.test import APITestCase

from seleniumrequests import Firefox
# from selenium.common import exceptions
# from selenium.webdriver.common.by import By
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from webdriver_manager.firefox import GeckoDriverManager

from geonode.base.populate_test_data import create_models
from geonode.geoserver.helpers import ogc_server_settings

from ..models import Upload

GEONODE_USER = 'admin'
GEONODE_PASSWD = 'admin'
GEOSERVER_URL = ogc_server_settings.LOCATION
GEOSERVER_USER, GEOSERVER_PASSWD = ogc_server_settings.credentials

logger = logging.getLogger(__name__)


@override_settings(
    ALLOWED_HOSTS=['*'],
    CSRF_COOKIE_SECURE=False,
    CSRF_COOKIE_HTTPONLY=False,
    CORS_ORIGIN_ALLOW_ALL=True,
    SESSION_COOKIE_SECURE=False
)
class UploadApiTests(StaticLiveServerTestCase, APITestCase):

    # port = 8000

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

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
            logger.exception(e)
        super().tearDownClass()

    def setUp(self):
        super(UploadApiTests, self).setUp()

        self.session_id = None
        self.csrf_token = None

        create_models(b'document')
        create_models(b'map')
        create_models(b'layer')

    def set_session_cookies(self, url=None):
        # selenium will set cookie domain based on current page domain
        self.selenium.get(url or f'{self.live_server_url}/')

        self.csrf_token = self.selenium.get_cookie('csrftoken')['value']
        self.session_id = self.selenium.get_cookie(settings.SESSION_COOKIE_NAME)['value']

        self.selenium.add_cookie(
            {'name': settings.SESSION_COOKIE_NAME, 'value': self.session_id, 'secure': False, 'path': '/'})
        self.selenium.add_cookie(
            {'name': 'csrftoken', 'value': self.csrf_token, 'secure': False, 'path': '/'})
        # refresh to exchange cookies with the server.
        self.selenium.refresh()

    def click_button(self, label):
        selector = f"//button[contains(., '{label}')]"
        self.selenium.find_element_by_xpath(selector).click()

    def login(self, username=GEONODE_USER, password=GEONODE_PASSWD):
        """ Method to login the GeoNode site"""
        from django.contrib.auth import authenticate
        assert authenticate(username=username, password=password)
        self.assertTrue(self.client.login(username=username, password=password))  # Native django test client

        url = urljoin(
            self.live_server_url,
            f"{reverse('account_login')}?next=/layers"
        )
        self.set_session_cookies(url)

        title = self.selenium.title
        current_url = self.selenium.current_url
        logger.error(f" ---- title: {title} / current_url: {current_url}")

        username_input = self.selenium.find_element_by_xpath('//input[@id="id_login"][@type="text"]')
        username_input.send_keys(username)
        password_input = self.selenium.find_element_by_xpath('//input[@id="id_password"][@type="password"]')
        password_input.send_keys(password)
        self.click_button("Sign In")

        title = self.selenium.title
        current_url = self.selenium.current_url
        logger.error(f" ---- title: {title} / current_url: {current_url}")
        # Wait until the response is received
        WebDriverWait(self.selenium, 10).until(
            # EC.url_changes(self.selenium.current_url)
            EC.title_contains("Explore Layers")
            # lambda x: title in self.selenium.title
        )

    def logout(self):
        self.selenium.get(f'{self.live_server_url}/account/logout/')
        self.selenium.find_element_by_xpath('//button[@type="submit"]').click()

    def upload_step(self, step=None):
        step = urljoin(
            self.live_server_url,
            reverse('data_upload', args=[step] if step else [])
        )
        return step

    def upload_file(self, _file):
        """ function that uploads a file, or a collection of files, to
        the GeoNode"""
        # self.login()

        spatial_files = ("dbf_file", "shx_file", "prj_file")
        base, ext = os.path.splitext(_file)
        params = {
            # make public since wms client doesn't do authentication
            # 'csrfmiddlewaretoken': self.csrf_token,
            'permissions': '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            'time': 'false',
            'charset': 'UTF-8'
        }
        # cookies = {
        #     settings.SESSION_COOKIE_NAME: self.session_id,
        #     'csrftoken': self.csrf_token
        # }
        # headers = {
        #     'X-CSRFToken': self.csrf_token,
        #     'X-Requested-With': 'XMLHttpRequest',
        #     'Set-Cookie': f'csrftoken={self.csrf_token}; sessionid={self.session_id}'
        # }
        # url = self.upload_step()
        # logger.error(f" ---- UPLOAD URL: {url} / cookies: {cookies} / headers: {headers}")

        # deal with shapefiles
        if ext.lower() == '.shp':
            for spatial_file in spatial_files:
                ext, _ = spatial_file.split('_')
                file_path = f"{base}.{ext}"
                # sometimes a shapefile is missing an extra file,
                # allow for that
                if os.path.exists(file_path):
                    params[spatial_file] = open(file_path, 'rb')
        elif ext.lower() == '.tif':
            file_path = base + ext
            params['tif_file'] = open(file_path, 'rb')

        with open(_file, 'rb') as base_file:
            params['base_file'] = base_file
            for name, value in params.items():
                if isinstance(value, IOBase):
                    params[name] = (os.path.basename(value.name), value)
            # response = self.selenium.request(
            #     'POST',
            #     url,
            #     data=params,
            #     headers=headers,
            #     cookies=cookies)
            url = urljoin(f"{reverse('uploads-list')}/", 'upload/')
            logger.error(f" ---- UPLOAD URL: {url}")
            response = self.client.put(url, data=params)

        # Closes the files
        for spatial_file in spatial_files:
            if isinstance(params.get(spatial_file), IOBase):
                params[spatial_file].close()

        if isinstance(params.get("tif_file"), IOBase):
            params['tif_file'].close()

        try:
            logger.error(f" -- response: {response.status_code} / {response.json()}")
            return response, response.json()
        except ValueError:
            logger.exception(
                ValueError(
                    f"probably not json, status {response.status_code} / {response.content}"))
            return response, response.content

    def test_uploads(self):
        """
        Ensure we can access the Uploads list.
        """
        # Try to upload a good raster file and check the session IDs
        self.assertTrue(self.client.login(username=GEONODE_USER, password=GEONODE_PASSWD))
        fname = os.path.join(GOOD_DATA, 'raster', 'relief_san_andres.tif')
        resp, data = self.upload_file(fname)
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(data['success'])
        self.assertIn('redirect_to', data)

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

        url = f"{reverse('uploads-detail', kwargs={'pk': response.data['uploads'][0]['id']})}/"
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, 200)
        upload_data = response.data['upload']
        self.assertIsNotNone(upload_data)
        self.assertEqual(upload_data['name'], 'relief_san_andres')
        logger.error(f" ---------- UPLOAD STATE: {upload_data['state']}")
        if upload_data['state'] != Upload.STATE_PROCESSED:
            self.assertLess(upload_data['progress'], 100.0)
            self.assertIsNone(upload_data['layer'])
            self.assertIsNotNone(upload_data['resume_url'])
            self.assertIsNotNone(upload_data['delete_url'])
            self.assertIn('uploadfile_set', upload_data)
            self.assertEqual(len(upload_data['uploadfile_set']), 0)
        else:
            self.assertEqual(upload_data['progress'], 100.0)
            self.assertIsNone(upload_data['resume_url'])
            self.assertIsNone(upload_data['delete_url'])
            self.assertIsNotNone(upload_data['layer'])
            self.assertIsNotNone(upload_data['layer']['detail_url'])

            self.assertNotIn('session', upload_data)
            response = self.client.get(f'{url}?full=true', format='json')
            self.assertEqual(response.status_code, 200)
            upload_data = response.data['upload']
            self.assertIsNotNone(upload_data)
            self.assertIn('session', upload_data)
            self.assertIn('uploadfile_set', upload_data)
            self.assertEqual(len(upload_data['uploadfile_set']), 1)

        self.assertIn('upload_dir', upload_data)
        self.assertIsNotNone(upload_data['upload_dir'])

        upload_dir = upload_data['upload_dir']

        self.assertTrue(os.path.exists(upload_dir) and os.path.isdir(upload_dir))
        self.assertGreaterEqual(len(os.listdir(upload_dir)), 1)

        response = self.client.get(upload_data['delete_url'], format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('uploads-list'), format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data['total'], 0)
        # Pagination
        self.assertEqual(len(response.data['uploads']), 0)
        logger.debug(response.data)

        self.assertFalse(os.path.exists(upload_dir))
