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

"""User can login using authentication feature tests."""
from urlparse import urljoin

from geonode import settings
from pytest_bdd import given, scenario, then, when


@scenario('login.feature', 'User can access login page')
def test_user_can_access_login_page():
    """User can access login page."""
    pass


@scenario('login.feature', 'Admin user')
def test_admin_user():
    """Admin user."""
    pass


@given('I have an admin account')
def admin_user():
    """I have an admin account."""


@given('A global administrator named "admin"')
def administrator_named_admin():
    """A global administrator named "admin"."""


@when('I go to the "login" page')
def go_to_login(browser):
    """I go to the "login" page."""
    browser.url = settings.SITEURL
    browser.visit(urljoin(browser.url, settings.LOGIN_URL))


@when('I fill in "Password" with "admin"')
def fill_password():
    """I fill in "Password" with "admin"."""


@when('I fill in "Username" with "admin"')
def fill_username():
    """I fill in "Username" with "admin"."""


@when('I go to the "login" page')
def go_to_login():
    """I go to the "login" page."""


@when('I press the "Log in" button')
def login_user(browser):
    """I press the "Log in" button."""
    browser.find_by_css('button[type=submit]').first.click()


@then('I see "Log in"')
def login_page(browser):
    """I see "Log in"."""
    browser.find_by_css('button[type=submit]')


@then('I should see "admin"')
def authenticated_page(browser):
    """I should see "admin"."""
    browser.find_by_xpath("//a[contains(@class, 'dropdown-toggle avatar')]")
