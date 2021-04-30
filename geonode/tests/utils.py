# -*- coding: utf-8 -*-
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

from geonode.tests.base import GeoNodeBaseTestSupport

import os
import copy
import time
import base64
import pickle
import requests
from urllib.parse import urlencode, urlsplit
from urllib.request import (
    urljoin,
    urlopen,
    build_opener,
    install_opener,
    HTTPCookieProcessor,
    HTTPPasswordMgrWithDefaultRealm,
    HTTPBasicAuthHandler,
)
from urllib.error import HTTPError, URLError
import logging
import contextlib

from io import IOBase
from bs4 import BeautifulSoup
from requests.packages.urllib3.util.retry import Retry
from requests_toolbelt.multipart.encoder import MultipartEncoder

from django.core import mail
from django.conf import settings
from django.db.models import signals
from django.urls import reverse
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.test.client import Client as DjangoTestClient

from geonode.maps.models import Layer
from geonode.geoserver.helpers import set_attributes
from geonode.geoserver.signals import geoserver_post_save
from geonode.notifications_helper import has_notifications, notifications

logger = logging.getLogger(__name__)


def upload_step(step=None):
    step = urljoin(
        settings.SITEURL,
        reverse('data_upload', args=[step] if step else [])
    )
    return step


class Client(DjangoTestClient):

    """client for making http requests"""

    def __init__(self, url, user, passwd, *args, **kwargs):
        super(Client, self).__init__(*args)

        self.url = url
        self.user = user
        self.passwd = passwd
        self.csrf_token = None
        self.response_cookies = None
        self._session = requests.Session()
        self._retry = Retry(
            total=3,
            read=3,
            connect=3,
            backoff_factor=0.3,
            status_forcelist=(104, 500, 502, 503, 504),
        )
        self._adapter = requests.adapters.HTTPAdapter(
            max_retries=self._retry,
            pool_maxsize=10,
            pool_connections=10)

        self._register_user()

    def _register_user(self):
        u, _ = get_user_model().objects.get_or_create(username=self.user)
        u.is_active = True
        u.email = 'admin@geonode.org'
        u.set_password(self.passwd)
        u.save()

    def make_request(self, path, data=None, ajax=False, debug=True, force_login=False):
        url = path if path.startswith("http") else self.url + path
        # logger.error(f" make_request ----------> url: {url}")

        if ajax:
            url += f"{'&' if '?' in url else '?'}force_ajax=true"
            self._session.headers['X_REQUESTED_WITH'] = "XMLHttpRequest"

        cookie_value = self._session.cookies.get(settings.SESSION_COOKIE_NAME)
        if force_login and cookie_value:
            self.response_cookies += f"; {settings.SESSION_COOKIE_NAME}={cookie_value}"

        if self.csrf_token:
            self._session.headers['X-CSRFToken'] = self.csrf_token

        if self.response_cookies:
            self._session.headers['cookie'] = self.response_cookies

        time.sleep(1.0)
        if data:
            for name, value in data.items():
                if isinstance(value, IOBase):
                    data[name] = (os.path.basename(value.name), value)

            encoder = MultipartEncoder(fields=data)
            self._session.headers['Content-Type'] = encoder.content_type
            self._session.mount(f"{urlsplit(url).scheme}://", self._adapter)
            self._session.verify = False
            self._action = getattr(self._session, 'post', None)

            # response = self._session.post(url, data=encoder)
            response = self._action(
                url=url,
                data=encoder,
                headers=self._session.headers,
                timeout=30,
                stream=False)
        else:
            self._session.mount(f"{urlsplit(url).scheme}://", self._adapter)
            self._session.verify = False
            self._action = getattr(self._session, 'get', None)

            # response = self._session.get(url)
            response = self._action(
                url=url,
                data=None,
                headers=self._session.headers,
                timeout=30,
                stream=False)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            message = ''
            if hasattr(ex, 'message'):
                if debug:
                    logger.error(f'error in request to {path}')
                    logger.error(ex.message)
                message = ex.message[ex.message.index(':') + 2:]
            else:
                message = str(ex)
            raise HTTPError(url, response.status_code, message, response.headers, None)

        return response

    def get(self, path, debug=True):
        return self.make_request(path, debug=debug)

    def login(self):
        """ Method to login the GeoNode site"""
        from django.contrib.auth import authenticate
        assert authenticate(username=self.user, password=self.passwd)
        self.csrf_token = self.get_csrf_token()
        params = {
            'csrfmiddlewaretoken': self.csrf_token,
            'login': self.user,
            'next': '/',
            'password': self.passwd}
        response = self.make_request(
            urljoin(
                settings.SITEURL,
                reverse('account_login')
            ),
            data=params
        )
        self.csrf_token = self.get_csrf_token()
        self.response_cookies = response.headers.get('Set-Cookie')

    def upload_file(self, _file):
        """ function that uploads a file, or a collection of files, to
        the GeoNode"""
        if not self.csrf_token:
            self.login()
        spatial_files = ("dbf_file", "shx_file", "prj_file")
        base, ext = os.path.splitext(_file)
        params = {
            # make public since wms client doesn't do authentication
            'permissions': '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            'csrfmiddlewaretoken': self.csrf_token,
            'time': 'true',
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
        elif ext.lower() == '.tif':
            file_path = base + ext
            params['tif_file'] = open(file_path, 'rb')

        with open(_file, 'rb') as base_file:
            params['base_file'] = base_file
            resp = self.make_request(
                upload_step(),
                data=params,
                ajax=True,
                force_login=True)

        # Closes the files
        for spatial_file in spatial_files:
            if isinstance(params.get(spatial_file), IOBase):
                params[spatial_file].close()

        if isinstance(params.get("tif_file"), IOBase):
            params['tif_file'].close()

        try:
            return resp, resp.json()
        except ValueError:
            logger.exception(ValueError(f"probably not json, status {resp.status_code}"))
            return resp, resp.content

    def get_html(self, path, debug=True):
        """ Method that make a get request and passes the results to bs4
        Takes a path and returns a tuple
        """
        resp = self.get(path, debug)
        return resp, BeautifulSoup(resp.content, features="lxml")

    def get_json(self, path):
        resp = self.get(path)
        return resp, resp.json()

    def get_csrf_token(self, last=False):
        """Get a csrf_token from the home page or read from the cookie jar
        based on the last response
        """
        if not last:
            self.get('/')
        return self._session.cookies.get("csrftoken")


def get_web_page(url, username=None, password=None, login_url=None):
    """Get url page possible with username and password.
    """

    if login_url:
        # Login via a form
        cookies = HTTPCookieProcessor()
        opener = build_opener(cookies)
        install_opener(opener)

        opener.open(login_url)

        try:
            token = [
                x.value for x in cookies.cookiejar if x.name == 'csrftoken'][0]
        except IndexError:
            return False, "no csrftoken"

        params = dict(username=username, password=password,
                      this_is_the_login_form=True,
                      csrfmiddlewaretoken=token,
                      )
        encoded_params = urlencode(params)

        with contextlib.closing(opener.open(login_url, encoded_params)) as f:
            f.read()
    elif username is not None:
        # Login using basic auth

        # Create password manager
        passman = HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, username, password)

        # create the handler
        authhandler = HTTPBasicAuthHandler(passman)
        opener = build_opener(authhandler)
        install_opener(opener)

    try:
        pagehandle = urlopen(url)
    except HTTPError as e:
        msg = ('The server couldn\'t fulfill the request. '
               'Error code: %s' % e.status_code)
        e.args = (msg,)
        raise
    except URLError as e:
        msg = f'Could not open URL "{url}": {e}'
        e.args = (msg,)
        raise
    else:
        page = pagehandle.read()

    return page


def check_layer(uploaded):
    """Verify if an object is a valid Layer.
    """
    msg = f'Was expecting layer object, got {type(uploaded)}'
    assert isinstance(uploaded, Layer), msg
    msg = f'The layer does not have a valid name: {uploaded.name}'
    assert len(uploaded.name) > 0, msg


class TestSetAttributes(GeoNodeBaseTestSupport):

    def setUp(self):
        super(TestSetAttributes, self).setUp()
        # Load users to log in as
        call_command('loaddata', 'people_data', verbosity=0)

    def test_set_attributes_creates_attributes(self):
        """ Test utility function set_attributes() which creates Attribute instances attached
            to a Layer instance.
        """
        # Creating a layer requires being logged in
        self.client.login(username='norman', password='norman')

        # Disconnect the geoserver-specific post_save signal attached to Layer creation.
        # The geoserver signal handler assumes things about the store where the Layer is placed.
        # this is a workaround.
        disconnected_post_save = signals.post_save.disconnect(geoserver_post_save, sender=Layer)

        # Create dummy layer to attach attributes to
        _l = Layer.objects.create(
            name='dummy_layer',
            bbox_x0=-180,
            bbox_x1=180,
            bbox_y0=-90,
            bbox_y1=90,
            srid='EPSG:4326')

        # Reconnect the signal if it was disconnected
        if disconnected_post_save:
            signals.post_save.connect(geoserver_post_save, sender=Layer)

        attribute_map = [
            ['id', 'Integer'],
            ['date', 'IntegerList'],
            ['enddate', 'Real'],
            ['date_as_date', 'xsd:dateTime'],
        ]

        # attribute_map gets modified as a side-effect of the call to set_attributes()
        expected_results = copy.deepcopy(attribute_map)

        # set attributes for resource
        set_attributes(_l, attribute_map)

        # 2 items in attribute_map should translate into 2 Attribute instances
        self.assertEqual(_l.attributes.count(), len(expected_results))

        # The name and type should be set as provided by attribute map
        for a in _l.attributes:
            self.assertIn([a.attribute, a.attribute_type], expected_results)


if has_notifications:
    from pinax.notifications.tests import get_backend_id
    from pinax.notifications.engine import send_all
    from pinax.notifications.models import NoticeQueueBatch

    class NotificationsTestsHelper(GeoNodeBaseTestSupport):

        """
        Helper class for notification tests
        This provides:
         *
        """

        def setup_notifications_for(self, notifications_list, user):
            notices = []
            email_id = get_backend_id("email")
            obc = notifications.models.NoticeSetting.objects.create
            ont = notifications.models.NoticeType.objects.get

            for name, label, desc in notifications_list:
                n = obc(user=user,
                        notice_type=ont(label=name),
                        medium=email_id,
                        send=True
                        )
                notices.append(n)
            return notices

        def clear_notifications_queue(self):
            send_all()
            mail.outbox = []

        def check_notification_out(self, notification_name, user):
            """
            Return True if user received notification
            """
            # with queued notifications we can detect notification types easier
            if settings.PINAX_NOTIFICATIONS_QUEUE_ALL:
                self.assertTrue(NoticeQueueBatch.objects.all().count() > 0)

                user.noticesetting_set.get(notice_type__label=notification_name)
                # we're looking for specific notification type/user combination, which is probably
                # at the end

                for queued_batch in NoticeQueueBatch.objects.all():
                    notices = pickle.loads(base64.b64decode(queued_batch.pickled_data))
                    for user_id, label, extra_context, sender in notices:
                        if label == notification_name and user_id == user.pk:
                            return True

                # clear notifications queue
                send_all()
                return False
            else:
                send_all()
                # empty outbox:/
                if not mail.outbox:
                    return False

                user.noticesetting_set.get(notice_type__label=notification_name)

                # unfortunatelly we can't use description check in subject, because subject is
                # generated from other template.
                # and notification.notice_type.description in msg.subject
                # last email should contain notification
                for msg in mail.outbox:
                    if user.email in msg.to:
                        return True
                return False
