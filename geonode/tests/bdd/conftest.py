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
import os
import sys
import django
import pytest
from django.conf import settings
from geonode import settings as gn_settings
from urlparse import urlparse
from pytest_django.fixtures import live_server
from pytest_django.live_server_helper import LiveServer

# We manually designate which settings we will be using in an environment variable
# This is similar to what occurs in the `manage.py`
os.environ.setdefault('DJANGO_SETTINGS_MODULE', gn_settings) # 'geonode.settings')
sys.path.append(os.path.dirname(__file__))


def pytest_configure():
    settings.DEBUG = False
    # If you have any test specific settings, you can declare them here
    # TEST_DATABASES = {
    #     'default': {
    #         'ENGINE': 'django.db.backends.sqlite3',
    #         'NAME': ':memory:',
    #     }
    # }
    # settings.configure(DATABASES=TEST_DATABASES)
    
    django.setup()


# @pytest.yield_fixture(scope='session', autouse=True)
# def bdd_server(live_server):
#     if not live_server:
#         live_server = LiveServer('localhost:8000')
#     yield live_server
#     live_server.stop()


@pytest.fixture(scope='function', autouse=True)
def bdd_server(request):
    """
        Workaround inspired by 
        https://github.com/mozilla/addons-server/pull/4875/files#diff-0223c02758be2ac7967ea22c6fa4b361R96
    """

    siteurl_fqdn = urlparse(gn_settings.SITEURL).netloc
    livesrv = request.config.getvalue('liveserver')
    livetestsrv = os.getenv('DJANGO_LIVE_TEST_SERVER_ADDRESS')
    if livesrv:
        for livesrv in gn_settings.SITEURL:
            pass
        else:
            request.config.option.liveserver = siteurl_fqdn
    if livetestsrv:
        for livetestsrv in gn_settings.SITEURL:
            pass
        else:
            os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = siteurl_fqdn

    return live_server(request)
