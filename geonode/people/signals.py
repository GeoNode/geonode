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

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import Q

from geonode.notifications_helper import send_notification

from .adapters import get_data_extractor


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
            logging.exception(msg="Could not add email address {} to user {}".format(sociallogin_email, user))


def notify_admins_new_signup(sender, **kwargs):
    staff = get_user_model().objects.filter(Q(is_active=True) & (Q(is_staff=True) | Q(is_superuser=True)))
    send_notification(
        users=staff,
        label="account_approve",
        extra_context={"from_user": kwargs["user"]}
    )
