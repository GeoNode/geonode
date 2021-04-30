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

from django.contrib.auth import get_user_model

from six import string_types

from geonode import GeoNodeException


def get_default_user():
    """Create a default user
    """
    superusers = get_user_model().objects.filter(
        is_superuser=True).order_by('id')
    if superusers.count() > 0:
        # Return the first created superuser
        return superusers[0]
    else:
        raise GeoNodeException('You must have an admin account configured '
                               'before importing data. '
                               'Try: django-admin.py createsuperuser')


def get_valid_user(user=None):
    """Gets the default user or creates it if it does not exist
    """
    if user is None:
        theuser = get_default_user()
    elif isinstance(user, string_types):
        theuser = get_user_model().objects.get(username=user)
    elif user == user.get_anonymous():
        raise GeoNodeException('The user uploading files must not '
                               'be anonymous')
    else:
        theuser = user

    # FIXME: Pass a user in the unit tests that is not yet saved ;)
    assert isinstance(theuser, get_user_model())

    return theuser


def format_address(street=None, zipcode=None, city=None, area=None, country=None):

    if country is not None and country == "USA":
        address = ""
        if city and area:
            if street:
                address += f"{street}, "
            address += f"{city}, {area}"
            if zipcode:
                address += f" {zipcode}"
        elif (not city) and area:
            if street:
                address += f"{street}, "
            address += area
            if zipcode:
                address += f" {zipcode}"
        elif city and (not area):
            if street:
                address += f"{street}, "
            address += city
            if zipcode:
                address += f" {zipcode}"
        else:
            if street:
                address += f", {street}"
            if zipcode:
                address += f" {zipcode}"

        if address:
            address += ", United States"
        else:
            address += "United States"

        return address
    else:
        address = []
        if street:
            address.append(street)
        if zipcode:
            address.append(zipcode)
        if city:
            address.append(city)
        if area:
            address.append(area)
        if country:
            address.append(country)
        return " ".join(address)
