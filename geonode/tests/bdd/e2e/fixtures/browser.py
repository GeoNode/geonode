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
from urllib.parse import urljoin

import pytest
from geonode import settings


@pytest.fixture
def base_url():
    return settings.SITE_URL


@pytest.fixture
def browser(browser, base_url, credentials):

    if credentials["login"]:
        browser.visit(urljoin(base_url, settings.LOGIN_URL))

        browser.fill("login", credentials["username"])
        browser.fill("password", credentials["password"])
        button = browser.find_by_css("button[type=submit]").first
        button.click()
    else:
        browser.visit(base_url)

    return browser
