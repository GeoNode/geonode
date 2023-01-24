#########################################################################
#
# Copyright (C) 2018 OSGeo
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

# import sys
from urllib.parse import urlparse

import django
import pytest
from django.conf import settings
from django.core.management import call_command
from geonode import settings as gn_settings

# from geonode.tests.bdd.e2e.factories.profile import SuperAdminProfileFactory

# We manually designate which settings we will be using in an environment variable
# This is similar to what occurs in the `manage.py`
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")
# sys.path.append(os.path.dirname(__file__))


def pytest_configure():
    settings.DEBUG = False
    # If you have any test specific settings, you can declare them here
    TEST_DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
    settings.DATABASES = TEST_DATABASES

    django.setup()


@pytest.fixture(scope="function", autouse=True)
def bdd_server(request, live_server):
    """
    Workaround inspired by
    https://github.com/mozilla/addons-server/pull/4875/files#diff-0223c02758be2ac7967ea22c6fa4b361R96
    """

    siteurl_fqdn = urlparse(gn_settings.SITEURL).netloc
    livesrv = request.config.getvalue("liveserver")
    livetestsrv = os.getenv("DJANGO_LIVE_TEST_SERVER_ADDRESS")
    if livesrv:
        for livesrv in gn_settings.SITEURL:
            pass
        else:
            request.config.option.liveserver = siteurl_fqdn
    if livetestsrv:
        for livetestsrv in gn_settings.SITEURL:
            pass
        else:
            os.environ["DJANGO_LIVE_TEST_SERVER_ADDRESS"] = siteurl_fqdn

    return live_server


@pytest.fixture(scope="function", autouse=True)
def geonode_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("loaddata", "initial_data.json")
        call_command("loaddata", "profiles_test_data.json")
        call_command("loaddata", "default_oauth_apps.json")


# @pytest.fixture(scope='function', autouse=True)
# def admin(db):
#     """Add admin user to the database."""
#     admintest = SuperAdminProfileFactory(username='admin')
#
#     return admintest
