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
import json
import base64
import pickle
import urllib
import urllib2
import logging
import contextlib

from bs4 import BeautifulSoup
from poster.streaminghttp import register_openers
from poster.encode import multipart_encode, MultipartParam

from django.core import mail
from django.conf import settings
from django.db.models import signals
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.test.client import Client as DjangoTestClient

from geonode.maps.models import Layer
from geonode.geoserver.helpers import set_attributes
from geonode.geoserver.signals import geoserver_post_save
from geonode.notifications_helper import has_notifications, notifications

logger = logging.getLogger(__name__)


def upload_step(step=None):
    step = reverse('data_upload', args=[step] if step else [])
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
        self.opener = self._init_url_opener()
        self.u, _ = get_user_model().objects.get_or_create(username=self.user)
        self.u.is_active = True
        self.u.email = 'admin@geonode.org'
        self.u.set_password(self.passwd)
        self.u.save()

    def _init_url_opener(self):
        self.cookies = urllib2.HTTPCookieProcessor()
        opener = register_openers()
        opener.add_handler(self.cookies)  # Add cookie handler
        return opener

    def _login(self, user, backend=None):
        from importlib import import_module
        from django.http import HttpRequest
        from django.contrib.auth import login
        engine = import_module(settings.SESSION_ENGINE)

        # Create a fake request to store login details.
        request = HttpRequest()

        request.session = engine.SessionStore()
        login(request, user, backend)

        # Save the session values.
        request.session.save()
        return request

    def make_request(self, path, data=None,
                     ajax=False, debug=True, force_login=False):
        url = path if path.startswith("http") else self.url + path
        if ajax:
            url += '&force_ajax=true' if '?' in url else '?force_ajax=true'
        request = None
        # Create a fake request to store login details.
        _request = None
        _session_id = None
        if force_login:
            session_cookie = settings.SESSION_COOKIE_NAME
            for cookie in self.cookies.cookiejar:
                if cookie.name == session_cookie:
                    _session_id = cookie.value
                    self.response_cookies += "; %s=%s" % (session_cookie, _session_id)
                    # _request = self.force_login(self.u)

                    # # Save the session values.
                    # _request.session.save()
                    # logger.info(_request.session)

                    # # Set the cookie to represent the session.
                    # logger.info(" -- session %s == %s " % (cookie.value, _request.session.session_key))
                    # cookie.value = _request.session.session_key
                    # cookie.expires = None
                    # self.cookies.cookiejar.set_cookie(cookie)

        if data:
            items = []
            # wrap post parameters
            for name, value in data.items():
                if isinstance(value, file):
                    # add file
                    items.append(MultipartParam.from_file(name, value.name))
                else:
                    if name == 'csrfmiddlewaretoken' and _request and _request.META['CSRF_COOKIE']:
                        value = _request.META['CSRF_COOKIE']
                        self.csrf_token = value
                        for cookie in self.cookies.cookiejar:
                            if cookie.name == 'csrftoken':
                                cookie.value = value
                                self.cookies.cookiejar.set_cookie(cookie)
                    items.append(MultipartParam(name, value))
                logger.debug(" MultipartParam: %s / %s: " % (name, value))
            datagen, headers = multipart_encode(items)
            request = urllib2.Request(url, datagen, headers)
        else:
            request = urllib2.Request(url=url)

        if self.csrf_token:
            request.add_header('X-CSRFToken', self.csrf_token)
        if self.response_cookies:
            request.add_header('cookie', self.response_cookies)
        if ajax:
            request.add_header('X_REQUESTED_WITH', 'XMLHttpRequest')

        try:
            return self.opener.open(request)
        except urllib2.HTTPError as ex:
            if not debug:
                raise
            logger.error('error in request to %s' % path)
            logger.error(ex.reason)
            logger.error(ex.read())
            raise

    def get(self, path, debug=True):
        return self.make_request(path, debug=debug)

    def force_login(self, user, backend=None):
        def get_backend():
            from django.contrib.auth import load_backend
            for backend_path in settings.AUTHENTICATION_BACKENDS:
                backend = load_backend(backend_path)
                if hasattr(backend, 'get_user'):
                    return backend_path
        if backend is None:
            backend = get_backend()
        user.backend = backend
        return self._login(user, backend)

    def login(self):
        """ Method to login the GeoNode site"""
        from django.contrib.auth import authenticate
        assert authenticate(username=self.user, password=self.passwd)

        self.csrf_token = self.get_csrf_token()
        params = {'csrfmiddlewaretoken': self.csrf_token,
                  'login': self.user,
                  'next': '/',
                  'password': self.passwd}
        response = self.make_request(
            reverse('account_login'),
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
                file_path = base + '.' + ext
                # sometimes a shapefile is missing an extra file,
                # allow for that
                if os.path.exists(file_path):
                    params[spatial_file] = open(file_path, 'rb')
        elif ext.lower() == '.tif':
            file_path = base + ext
            params['tif_file'] = open(file_path, 'rb')

        base_file = open(_file, 'rb')
        params['base_file'] = base_file
        resp = self.make_request(
            upload_step(),
            data=params,
            ajax=True,
            force_login=True)
        data = resp.read()
        try:
            return resp, json.loads(data)
        except ValueError:
            logger.exception(ValueError(
                'probably not json, status %s' %
                resp.getcode(),
                data))
            return resp, data

    def get_html(self, path, debug=True):
        """ Method that make a get request and passes the results to bs4
        Takes a path and returns a tuple
        """
        resp = self.get(path, debug)
        return resp, BeautifulSoup(resp.read())

    def get_json(self, path):
        resp = self.get(path)
        return resp, json.loads(resp.read())

    def get_csrf_token(self, last=False):
        """Get a csrf_token from the home page or read from the cookie jar
        based on the last response
        """
        if not last:
            self.get('/')
        csrf = [c for c in self.cookies.cookiejar if c.name == 'csrftoken']
        return csrf[0].value if csrf else None


def get_web_page(url, username=None, password=None, login_url=None):
    """Get url page possible with username and password.
    """

    if login_url:
        # Login via a form
        cookies = urllib2.HTTPCookieProcessor()
        opener = urllib2.build_opener(cookies)
        urllib2.install_opener(opener)

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
        encoded_params = urllib.urlencode(params)

        with contextlib.closing(opener.open(login_url, encoded_params)) as f:
            f.read()
    elif username is not None:
        # Login using basic auth

        # Create password manager
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, username, password)

        # create the handler
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)

    try:
        pagehandle = urllib2.urlopen(url)
    except urllib2.HTTPError as e:
        msg = ('The server couldn\'t fulfill the request. '
               'Error code: %s' % e.code)
        e.args = (msg,)
        raise
    except urllib2.URLError as e:
        msg = 'Could not open URL "%s": %s' % (url, e)
        e.args = (msg,)
        raise
    else:
        page = pagehandle.read()

    return page


def check_layer(uploaded):
    """Verify if an object is a valid Layer.
    """
    msg = ('Was expecting layer object, got %s' % (type(uploaded)))
    assert isinstance(uploaded, Layer), msg
    msg = ('The layer does not have a valid name: %s' % uploaded.name)
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
        self.assertEquals(_l.attributes.count(), len(expected_results))

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

                msg = mail.outbox[-1]
                user.noticesetting_set.get(notice_type__label=notification_name)

                # unfortunatelly we can't use description check in subject, because subject is
                # generated from other template.
                # and notification.notice_type.description in msg.subject
                # last email should contain notification
                return user.email in msg.to
