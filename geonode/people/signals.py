#########################################################################
#
# Copyright (C) 2017 OSGeo
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

"""Signal handlers pertaining to the people app

Some of these signals deal with authentication related workflows.

"""
import logging
import traceback

from uuid import uuid1

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import Q

from geonode.base.auth import (get_or_create_token,
                               delete_old_tokens,
                               set_session_token,
                               remove_session_token)

from geonode.groups.models import GroupProfile
from geonode.groups.conf import settings as groups_settings
from geonode.notifications_helper import send_notification

from .adapters import get_data_extractor

logger = logging.getLogger(__name__)


def _add_user_to_registered_members(user):
    if groups_settings.AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME:
        group_name = groups_settings.REGISTERED_MEMBERS_GROUP_NAME
        groupprofile = GroupProfile.objects.filter(slug=group_name).first()
        if groupprofile:
            groupprofile.join(user)


def _remove_user_from_registered_members(user):
    if groups_settings.AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME:
        group_name = groups_settings.REGISTERED_MEMBERS_GROUP_NAME
        groupprofile = GroupProfile.objects.filter(slug=group_name).first()
        if groupprofile:
            groupprofile.leave(user)


def do_login(sender, user, request, **kwargs):
    """
    Take action on user login. Generate a new user access_token to be shared
    with GeoServer, and store it into the request.session
    """
    if user and user.is_authenticated:
        token = None
        try:
            token = get_or_create_token(user)
        except Exception:
            u = uuid1()
            token = u.hex
            tb = traceback.format_exc()
            logger.debug(tb)

        set_session_token(request.session, token)

        if groups_settings.AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_AT == 'login':
            _add_user_to_registered_members(user)


def do_logout(sender, user, request, **kwargs):
    if 'access_token' in request.session:
        try:
            delete_old_tokens(user)
        except Exception:
            tb = traceback.format_exc()
            logger.debug(tb)
        remove_session_token(request.session)
        request.session.modified = True


def update_user_email_addresses(sender, **kwargs):
    sociallogin = kwargs["sociallogin"]
    user = sociallogin.user
    extractor = get_data_extractor(sociallogin.account.provider)
    try:
        sociallogin_email = extractor.extract_email(
            sociallogin.account.extra_data)
    except NotImplementedError:
        sociallogin_email = None
    if sociallogin_email is not None:
        try:
            EmailAddress.objects.add_email(
                request=None, user=user, email=sociallogin_email, confirm=False)
        except IntegrityError:
            logging.exception(msg=f"Could not add email address {sociallogin_email} to user {user}")


def notify_admins_new_signup(sender, **kwargs):
    staff = get_user_model().objects.filter(Q(is_active=True) & (Q(is_staff=True) | Q(is_superuser=True)))
    send_notification(
        users=staff,
        label="account_approve",
        extra_context={"from_user": kwargs["user"]}
    )

    if groups_settings.AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_AT == 'registration':
        _add_user_to_registered_members(kwargs["user"])


def profile_post_save(instance, sender, **kwargs):
    """
    Make sure the user belongs by default to the anonymous group.
    This will make sure that anonymous permissions will be granted to the new users.
    """
    from django.contrib.auth.models import Group
    anon_group, created = Group.objects.get_or_create(name='anonymous')
    instance.groups.add(anon_group)

    if groups_settings.AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_AT == 'activation':
        created = kwargs.get('created', False)
        became_active = instance.is_active and (not instance._previous_active_state or created)
        if became_active:
            _add_user_to_registered_members(instance)
        elif not instance.is_active:
            _remove_user_from_registered_members(instance)

    # do not create email, when user-account signup code is in use
    if getattr(instance, '_disable_account_creation', False):
        return
