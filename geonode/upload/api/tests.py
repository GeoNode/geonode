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
import django
import logging

from io import IOBase
from gisdata import GOOD_DATA
from urllib.request import urljoin

from django.conf import settings

from django.urls import reverse
from django.conf.urls import url, include
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from rest_framework.test import APITestCase, URLPatternsTestCase

from seleniumrequests import Firefox
# from selenium.common import exceptions
# from selenium.webdriver.common.by import By
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from webdriver_manager.firefox import GeckoDriverManager

from geonode.api.urls import router
from geonode.maps.views import map_embed
from geonode.services.views import services
from geonode.geoapps.views import geoapp_edit
from geonode.layers.views import layer_upload, layer_embed, layer_detail

from geonode import geoserver
from geonode.utils import check_ogc_backend
from geonode.base.populate_test_data import create_models

from geonode.geoserver.helpers import ogc_server_settings

GEONODE_USER = 'admin'
GEONODE_PASSWD = 'admin'
GEOSERVER_URL = ogc_server_settings.LOCATION
GEOSERVER_USER, GEOSERVER_PASSWD = ogc_server_settings.credentials

logger = logging.getLogger(__name__)


class UploadApiTests(StaticLiveServerTestCase, APITestCase, URLPatternsTestCase):

    port = 8000

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

    urlpatterns = [
        url(r'^$',
            TemplateView.as_view(template_name='index.html'),
            name='home'),
        url(r'^help/$',
            TemplateView.as_view(template_name='help.html'),
            name='help'),
        url(r'^developer/$',
            TemplateView.as_view(
                template_name='developer.html'),
            name='developer'),
        url(r'^about/$',
            TemplateView.as_view(template_name='about.html'),
            name='about'),
        url(r'^privacy_cookies/$',
            TemplateView.as_view(template_name='privacy-cookies.html'),
            name='privacy-cookies'),
        url(r'^/', include('geonode.proxy.urls')),
        url(r"^account/", include("allauth.urls")),
        url(r'^base/', include('geonode.base.urls')),
        url(r'^people/', include('geonode.people.urls')),
        url(r'^api/v2/', include(router.urls)),
        url(r'^api/v2/', include('geonode.api.urls')),
        url(r'^api/v2/api-auth/', include('rest_framework.urls', namespace='geonode_rest_framework')),
        url(r'^upload$', layer_upload, name='layer_upload'),
        url(r'^layers/$',
            TemplateView.as_view(template_name='layers/layer_list.html'),
            {'facet_type': 'layers', 'is_layer': True},
            name='layer_browse'),
        url(r'^maps/$',
            TemplateView.as_view(template_name='maps/map_list.html'),
            {'facet_type': 'maps', 'is_map': True},
            name='maps_browse'),
        url(r'^documents/$',
            TemplateView.as_view(template_name='documents/document_list.html'),
            {'facet_type': 'documents', 'is_document': True},
            name='document_browse'),
        url(r'^apps/$',
            TemplateView.as_view(template_name='apps/app_list.html'),
            {'facet_type': 'geoapps'},
            name='apps_browse'),
        url(r'^groups/$',
            TemplateView.as_view(template_name='groups/group_list.html'),
            name='group_list'),
        url(r'^categories/$',
            TemplateView.as_view(template_name="groups/category_list.html"),
            name="group_category_list"),
        url(r'^search/$',
            TemplateView.as_view(template_name='search/search.html'),
            name='search'),
        url(r'^services/$', services, name='services'),
        url(r'^invitations/', include(
            'geonode.invitations.urls', namespace='geonode.invitations')),
        url(r'^i18n/', include(django.conf.urls.i18n), name="i18n"),
        url(r'^jsi18n/$', JavaScriptCatalog.as_view(), {}, name='javascript-catalog'),
        url(r'^maps/(?P<mapid>[^/]+)/embed$', map_embed, name='map_embed'),
        url(r'^layers/(?P<layername>[^/]+)/embed$', layer_embed, name='layer_embed'),
        url(r'^layers/(?P<layername>[^/]*)$', layer_detail, name="layer_detail"),
        url(r'^apps/(?P<geoappid>[^/]+)/embed$', geoapp_edit, {'template': 'apps/app_embed.html'}, name='geoapp_embed'),
    ]

    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        from geonode.geoserver.views import layer_acls, resolve_user
        urlpatterns += [
            url(r'^layers/acls/?$', layer_acls, name='layer_acls'),
            url(r'^layers/acls_dep/?$', layer_acls, name='layer_acls_dep'),
            url(r'^layers/resolve_user/?$', resolve_user, name='layer_resolve_user'),
            url(r'^layers/resolve_user_dep/?$', resolve_user, name='layer_resolve_user_dep'),
        ]
        from geonode.upload import views as upload_views
        urlpatterns += [  # 'geonode.upload.views',
            url(r'^upload/new/$', upload_views.UploadFileCreateView.as_view(),
                name='data_upload_new'),
            url(r'^upload/progress$', upload_views.data_upload_progress,
                name='data_upload_progress'),
            url(r'^upload/(?P<step>\w+)?$', upload_views.view, name='data_upload'),
            url(r'^upload/delete/(?P<id>\d+)?$',
                upload_views.delete, name='data_upload_delete'),
            url(r'^upload/remove/(?P<pk>\d+)$',
                upload_views.UploadFileDeleteView.as_view(), name='data_upload_remove'),
            url(r'^', include('geonode.upload.api.urls')),
        ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

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

        settings.SITEURL = f'{self.live_server_url}/'
        settings.ACCOUNT_LOGIN_REDIRECT_URL = self.live_server_url
        settings.ACCOUNT_LOGOUT_REDIRECT_URL = self.live_server_url

        settings.ALLOWED_HOSTS = ['*'],
        settings.CSRF_COOKIE_SECURE = False,
        settings.CSRF_COOKIE_HTTPONLY = False,
        settings.CORS_ORIGIN_ALLOW_ALL = True,
        settings.SESSION_COOKIE_SECURE = False,
        settings.OGC_REQUEST_TIMEOUT = 1

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
            # EC.title_contains("Explore Layers")
            EC.title_contains(title)
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
                file_path = base + '.' + ext
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
            logger.error(f" -- response: {response.status_code} / {response.json}")
            return response, response.json
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
        self.assertEqual(response.data['total'], 8)
        # Pagination
        self.assertEqual(len(response.data['uploads']), 8)
        logger.debug(response.data)
