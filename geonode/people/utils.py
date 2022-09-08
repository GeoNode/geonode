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

from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from geonode import GeoNodeException
from geonode.groups.models import GroupProfile, GroupMember
from geonode.groups.conf import settings as groups_settings


def get_default_user():
    """Create a default user
    """
    superusers = get_user_model().objects.filter(
        is_superuser=True).order_by('id')
    if superusers.exists():
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
    elif isinstance(user, str):
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


def get_available_users(user):
    """Filters users a given user can see.
    eg all users from public groups and all users in private groups as a given user.

    Args:
        user (settings.AUTH_USER_MODEL): User object

    Returns:
        Queryset: Queryset of users a given user can see
    """
    if user.is_superuser:
        return get_user_model().objects.exclude(Q(username='AnonymousUser') | Q(is_active=False))

    member_ids = []
    if not user.is_anonymous:
        # Append current user profile in the list of users to be returned
        member_ids.extend([user.id])

    # Only return user that are members of any group profile the current user is member of
    member_ids.extend(list(GroupMember.objects.filter(
        group__in=GroupProfile.objects.filter(
            Q(access='public') | Q(group__in=user.groups.all()))
    ).select_related('user').values_list('user__id', flat=True)))
    if Group.objects.filter(name=groups_settings.REGISTERED_MEMBERS_GROUP_NAME).exists():
        # Retrieve all members in Registered member's group
        rm_group = Group.objects.get(name=groups_settings.REGISTERED_MEMBERS_GROUP_NAME)
        users_ids = list(rm_group.user_set.values_list('id', flat=True))
        member_ids.extend(users_ids)

    return get_user_model().objects.filter(id__in=member_ids)
