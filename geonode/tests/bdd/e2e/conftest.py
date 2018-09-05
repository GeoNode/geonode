# -*- coding: utf-8 -*-
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
import signal
from urlparse import urljoin

import pytest
from geonode import settings as gn_settings
from geonode.tests.bdd import __file__ as bdd_path
from splinter import Browser

# @pytest.fixture(scope='session')
# def pytestbdd_selenium_speed():
#     return 0.5

# @pytest.fixture(scope='session')
# def splinter_implicit_wait():
#     return True


@pytest.yield_fixture(scope='function', autouse=True)
def en_browser(browser, bdd_server):
    """Browser login page from live server."""
    browser = Browser('phantomjs')
    en_browser = browser
    en_browser.visit(urljoin(bdd_server.url, gn_settings.LOGIN_URL))
    yield en_browser
    try:
        # kill the specific phantomjs child proc
        en_browser.service.process.send_signal(signal.SIGTERM)
    except BaseException:
        pass
    try:
        # quit the node proc
        en_browser.quit()
    except BaseException:
        pass


@pytest.fixture
def pytestbdd_feature_base_dir():
    """Feature files base directory."""

    return os.path.join(
        os.path.dirname(bdd_path),
        'features'
    )
