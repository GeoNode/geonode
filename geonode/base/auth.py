# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2019 OSGeo
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

import datetime
import base64
import logging
import traceback

from django.utils import timezone
from django.conf import settings
from django.contrib.auth import authenticate
from oauth2_provider.models import AccessToken, get_application_model
from oauthlib.common import generate_token

logger = logging.getLogger(__name__)


def make_token_expiration(seconds=86400):
    _expire_seconds = getattr(settings, 'ACCESS_TOKEN_EXPIRE_SECONDS', seconds)
    _expire_time = datetime.datetime.now(timezone.get_current_timezone())
    _expire_delta = datetime.timedelta(seconds=_expire_seconds)
    return _expire_time + _expire_delta


def create_auth_token(user, client="GeoServer"):
    expires = make_token_expiration()
    Application = get_application_model()
    app = Application.objects.get(name=client)
    (access_token, created) = AccessToken.objects.get_or_create(
        user=user,
        application=app,
        expires=expires,
        token=generate_token())
    return access_token


def extend_token(token):
    access_token = AccessToken.objects.get(id=token.id)
    expires = make_token_expiration()
    access_token.expires = expires
    access_token.save()


def get_auth_token(user, client="GeoServer"):
    Application = get_application_model()
    app = Application.objects.get(name=client)
    access_token = AccessToken.objects.filter(user=user, application=app).order_by('-expires').first()
    return access_token


def get_or_create_token(user, client="GeoServer"):
    application = get_application_model()
    app = application.objects.get(name=client)

    # Let's create the new AUTH TOKEN
    existing_token = None
    try:
        existing_token = AccessToken.objects.filter(user=user, application=app).order_by('-expires').first()
        if existing_token and existing_token.is_expired():
            existing_token.delete()
            existing_token = None
    except BaseException:
        existing_token = None
        tb = traceback.format_exc()
        if tb:
            logger.debug(tb)

    if not existing_token:
        token = create_auth_token(user, client)
    else:
        token = existing_token

    return token


def delete_old_tokens(user, client='GeoServer'):
    application = get_application_model()
    app = application.objects.get(name=client)

    # Lets delete the old one
    try:
        old_tokens = AccessToken.objects.filter(user=user, application=app).order_by('-expires')
        for old in old_tokens:
            if old.is_expired():
                old.delete()
    except BaseException:
        tb = traceback.format_exc()
        if tb:
            logger.debug(tb)


def get_token_from_auth_header(auth_header):
    if 'Basic' in auth_header:
        encoded_credentials = auth_header.split(' ')[1]  # Removes "Basic " to isolate credentials
        decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8").split(':')
        username = decoded_credentials[0]
        password = decoded_credentials[1]
        # if the credentials are correct, then the feed_bot is not None, but is a User object.
        user = authenticate(username=username, password=password)
        return get_auth_token(user)
    elif 'Bearer' in auth_header:
        return auth_header.replace('Bearer ', '')
    return None


def set_session_token(session, token):
    session['access_token'] = str(token)


def get_session_token(session):
    return session.get('access_token', None)


def get_token_object_from_session(session):
    if 'access_token' in session:
        try:
            return AccessToken.objects.get(token=get_session_token(session))
        except BaseException:
            del session['access_token']
            session.modified = True
            return None
    return None


def remove_session_token(session):
    if 'access_token' in session:
        del session['access_token']
