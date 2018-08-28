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

from allauth.account.utils import user_field, user_email, user_username

from ..utils import json_response


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


def extract_headers(request):
    """
    Extracts headers from the Django request object
    :param request: The current django.http.HttpRequest object
    :return: a dictionary with OAuthLib needed headers
    """
    headers = request.META.copy()
    if "wsgi.input" in headers:
        del headers["wsgi.input"]
    if "wsgi.errors" in headers:
        del headers["wsgi.errors"]
    if "HTTP_AUTHORIZATION" in headers:
        headers["Authorization"] = headers["HTTP_AUTHORIZATION"]

    return headers


@csrf_exempt
def user_info(request):
    headers = extract_headers(request)
    user = request.user

    if not user:
        out = {'success': False,
               'status': 'error',
               'errors': {'user': ['User is not authenticated']}
               }
        return json_response(out, status=401)

    if 'Authorization' not in headers and 'Bearer' not in headers["Authorization"]:
        out = {'success': False,
               'status': 'error',
               'errors': {'auth': ['No token provided.']}
               }
        return json_response(out, status=403)

    groups = [group.name for group in user.groups.all()]
    if user.is_superuser:
        groups.append("admin")

    user_info = json.dumps({
        "sub": str(user.id),
        "name": " ".join([user_field(user, 'first_name'), user_field(user, 'last_name')]),
        "given_name": user_field(user, 'first_name'),
        "family_name": user_field(user, 'last_name'),
        "email": user_email(user),
        "preferred_username": user_username(user),
        "groups": groups
    })

    response = HttpResponse(
        user_info,
        content_type="application/json"
    )
    response['Cache-Control'] = 'no-store'
    response['Pragma'] = 'no-cache'
    return response


@csrf_exempt
def verify_token(request):
    """
    TODO: Check IP whitelist / blacklist
    Verifies the velidity of an OAuth2 Access Token
    and returns associated User's details
    """

    """
    No need to check authentication (see Issue #2815)
    if (not request.user.is_authenticated()):
        return HttpResponse(
            json.dumps({
                'error': 'unauthorized_request'
            }),
            status=403,
            content_type="application/json"
        )
    """

    if (request.POST and 'token' in request.POST):
        token = None
        try:
            access_token = request.POST.get('token')
            token = verify_access_token(access_token)
        except Exception as e:
            return HttpResponse(
                json.dumps({
                    'error': str(e)
                }),
                status=403,
                content_type="application/json"
            )

        if token:
            token_info = json.dumps({
                'client_id': token.application.client_id,
                'user_id': token.user.id,
                'username': token.user.username,
                'issued_to': token.user.username,
                'access_token': access_token,
                'email': token.user.email,
                'verified_email': 'true',
                'access_type': 'online',
                'expires_in': (token.expires - timezone.now()).total_seconds() * 1000
            })

            response = HttpResponse(
                token_info,
                content_type="application/json"
            )
            response["Authorization"] = ("Bearer %s" % access_token)
            return response
        else:
            return HttpResponse(
                json.dumps({
                    'error': 'No access_token from server.'
                }),
                status=403,
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
