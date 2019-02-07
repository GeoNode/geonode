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
import socket

import requests
from django.conf import settings
from kombu import Connection
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

requests.packages.urllib3.disable_warnings()


def requests_retry(retries=3,
                   backoff_factor=0.5,
                   status_forcelist=(502, 503, 504),
                   session=None):
    session = session or requests.Session()
    # disable ssl verify
    session.verify = False
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        method_whitelist=frozenset(['GET', 'POST', 'PUT', 'DELETE', 'HEAD']))
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def geoserver_requests_session():
    from .helpers import ogc_server_settings
    _user, _password = ogc_server_settings.credentials
    session = requests.Session()
    session.auth = (_user, _password)
    session = requests_retry(session=session)
    return session


def get_broker_url():
    broker_url = getattr(settings, 'CELERY_BROKER_URL', None)
    if not broker_url:
        broker_url = getattr(settings, 'BROKER_URL', None)
    return broker_url


def _check_async():
    return getattr(settings, 'ASYNC_SIGNALS', False)


def check_broker_status():
    running = False
    broker_url = get_broker_url()
    if 'memory' not in broker_url and _check_async():
        try:
            conn = Connection(broker_url)
            conn.ensure_connection(max_retries=3)
            running = True
        except socket.error:
            running = _check_async()

    return running


def test_running():
    return getattr(settings, 'TEST', False) or getattr(settings, 'INTEGRATION',
                                                       False)


celery_enabled = check_broker_status()
