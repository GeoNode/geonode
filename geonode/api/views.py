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

import json

from django.utils import timezone
from oauth2_provider.models import AccessToken
from oauth2_provider.exceptions import OAuthToolkitError, FatalClientError
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse

from guardian.models import Group


def verify_access_token(key):
    try:
        token = AccessToken.objects.get(token=key)

        if not token.is_valid():
            raise OAuthToolkitError('AccessToken is not valid.')
        if token.is_expired():
            raise OAuthToolkitError('AccessToken has expired.')
    except AccessToken.DoesNotExist:
        raise FatalClientError("AccessToken not found at all.")

    return token


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@csrf_exempt
def verify_token(request):
    """
    TODO: Check IP whitelist / blacklist
    Verifies the velidity of an OAuth2 Access Token
    and returns associated User's details
    """
    if (not request.user.is_authenticated()):
        return HttpResponse(
            json.dumps({
                'error': 'unauthorized_request'
            }),
            status=403,
            content_type="application/json"
        )

    if (request.POST and request.POST['token']):
        try:
            token = verify_access_token(request.POST['token'])
        except Exception, e:
            return HttpResponse(
                json.dumps({
                    'error': str(e)
                }),
                status=403,
                content_type="application/json"
            )

        return HttpResponse(
            json.dumps({
                'client_id': token.application.client_id,
                'issued_to': token.user.username,
                'user_id': token.user.id,
                'email': token.user.email,
                'verified_email': 'true',
                'access_type': 'online',
                'expires_in': (token.expires - timezone.now()).total_seconds() * 1000
            }),
            content_type="application/json"
        )

    return HttpResponse(
        json.dumps({
            'error': 'invalid_request'
        }),
        status=403,
        content_type="application/json"
    )


@csrf_exempt
def roles(request):
    """
    Check IP whitelist / blacklist
    """
    if settings.AUTH_IP_WHITELIST and not get_client_ip(request) in settings.AUTH_IP_WHITELIST:
        return HttpResponse(
            json.dumps({
                'error': 'unauthorized_request'
            }),
            status=403,
            content_type="application/json"
        )

    groups = [group.name for group in Group.objects.all()]
    groups.append("admin")

    return HttpResponse(
        json.dumps({
            'groups': groups
        }),
        content_type="application/json"
    )


@csrf_exempt
def users(request):
    """
    Check IP whitelist / blacklist
    """
    if settings.AUTH_IP_WHITELIST and not get_client_ip(request) in settings.AUTH_IP_WHITELIST:
        return HttpResponse(
            json.dumps({
                'error': 'unauthorized_request'
            }),
            status=403,
            content_type="application/json"
        )

    user_name = request.path_info.rsplit('/', 1)[-1]
    User = get_user_model()

    if user_name is None or not user_name or user_name == "users":
        users = [user for user in User.objects.all()]
    else:
        users = [user for user in User.objects.filter(username=user_name)]

        if not users:
            # Try using the user email
            users = [user for user in User.objects.filter(email=user_name)]

    json_object = []
    for user in users:
        groups = [group.name for group in user.groups.all()]
        if user.is_superuser:
            groups.append("admin")

        json_object.append({
            'username': user.username,
            'groups': groups
        })

    return HttpResponse(
        json.dumps({
            'users': json_object
        }),
        content_type="application/json"
    )


@csrf_exempt
def admin_role(request):
    """
    Check IP whitelist / blacklist
    """
    if settings.AUTH_IP_WHITELIST and not get_client_ip(request) in settings.AUTH_IP_WHITELIST:
        return HttpResponse(
            json.dumps({
                'error': 'unauthorized_request'
            }),
            status=403,
            content_type="application/json"
        )

    return HttpResponse(
        json.dumps({
            'adminRole': 'admin'
        }),
        content_type="application/json"
    )
