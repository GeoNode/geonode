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

"""User can login using authentication feature tests."""

import pytest
from django.contrib.auth import get_user_model
from pytest_bdd import given, scenario, then, when


# https://github.com/pytest-dev/pytest-django/issues/329
@pytest.mark.django_db(transaction=True)  # , serialized_rollback=True)
@scenario('features/login.feature', 'User can access login page')
def test_user_can_access_login_page(db, geonode_db_setup):
    """User can access login page."""
    # pass


@pytest.mark.django_db(transaction=True)  # , serialized_rollback=True)
@scenario('features/login.feature', 'Admin user')
def test_admin_user():
    """Admin user."""
    # pass


@given('I have an admin account')
def admin_user():
    """I have an admin account."""


@given('A global administrator named "admin"')
def administrator_named_admin():
    """A global administrator named "admin"."""
    admin = get_user_model().objects.filter(username='admin')
    assert admin.exists() is True


@when('I go to the "login" page')
def go_to_login(en_browser):
    """I go to the "login" page."""
    assert en_browser.is_text_present('Username')
    assert en_browser.is_text_present('Password')


@when('I fill in "Username" with "admin"')
def fill_username(en_browser):
    """I fill in "Username" with "admin"."""
    assert en_browser.is_text_present('Username')
    en_browser.fill('login', 'admin')


@when('I fill in "Password" with "admin"')
def fill_password(en_browser):
    """I fill in "Password" with "admin"."""
    assert en_browser.is_text_present('Password')
    en_browser.fill('password', 'admin')


@when('I press the "Log in" button')
def login_user(en_browser):
    """I press the "Log in" button."""
    en_browser.find_by_css('button[type=submit]').first.click()


@then('I see "Log in"')
def login_page(en_browser):
    """I see "Log in"."""
    assert en_browser.find_by_css('button[type=submit]')


@then('I should see "admin"')
def authenticated_page(en_browser):
    """I should see "admin"."""
    assert en_browser.find_by_xpath(
        "//a[contains(@class, 'dropdown-toggle avatar')]")
