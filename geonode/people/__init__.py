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
from uuid import uuid4

from allauth.account.signals import user_signed_up
from allauth.socialaccount.signals import social_account_added
from django.utils.translation import ugettext_noop as _
from geonode.notifications_helper import NotificationsAppConfigBase

from . import signals


class PeopleAppConfig(NotificationsAppConfigBase):
    name = 'geonode.people'
    NOTIFICATIONS = (("user_follow", _("User following you"), _("Another user has started following you"),),
                     ("account_approve", _("User requested access"),
                      _("A new user has requested access to the site"),),
                     ("account_active", _("Account activated"),
                      _("This account is now active and can log in the site"),),
                     )

    def ready(self):
        """ Connect relevant signals to their corresponding handlers. """
        social_account_added.connect(
            signals.update_user_email_addresses,
            dispatch_uid=str(uuid4()),
            weak=False
        )
        user_signed_up.connect(
            signals.notify_admins_new_signup,
            dispatch_uid=str(uuid4()),
            weak=False
        )


default_app_config = 'geonode.people.PeopleAppConfig'
