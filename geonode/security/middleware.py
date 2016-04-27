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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from re import compile
from guardian.shortcuts import get_anonymous_user


class LoginRequiredMiddleware(object):

    """
    Requires a user to be logged in to access any page that is not white-listed.
    """

    white_list_paths = (
        reverse('account_login'),
        reverse('forgot_username'),
        reverse('help'),
        reverse('jscat'),
        reverse('lang'),
        reverse('layer_acls'),
        reverse('layer_acls_dep'),
        reverse('layer_resolve_user'),
        reverse('layer_resolve_user_dep'),
        '/account/(?!.*(?:signup))',
        # block unauthenticated users from creating new accounts.
        '/static/*',
    )

    white_list = map(
        compile,
        white_list_paths +
        getattr(
            settings,
            "AUTH_EXEMPT_URLS",
            ()))
    redirect_to = reverse('account_login')

    def process_request(self, request):
        if not request.user.is_authenticated(
        ) or request.user == get_anonymous_user():
            if not any(path.match(request.path) for path in self.white_list):
                return HttpResponseRedirect(
                    '{login_path}?next={request_path}'.format(
                        login_path=self.redirect_to,
                        request_path=request.path))
