import datetime
import base64

from django.utils import timezone
from django.conf import settings
from django.contrib.auth import authenticate
from oauth2_provider.models import AccessToken, get_application_model
from oauthlib.common import generate_token

def make_token_expiration():
    _expire_seconds = getattr(settings, 'ACCESS_TOKEN_EXPIRE_SECONDS', 86400)
    _expire_time = datetime.datetime.now(timezone.get_current_timezone())
    _expire_delta = datetime.timedelta(seconds=_expire_seconds)
    return _expire_time + _expire_delta

def create_auth_token(user, client="GeoServer"):
    expires = make_token_expiration()
    Application = get_application_model()
    app = Application.objects.get(name=client)
    access_token = AccessToken.objects.get(
        user=user,
        application=app,
        expires=expires,
        token=generate_token())
    return access_token

def extend_oauth_token(token):
    access_token = AccessToken.objects.get(id=token.id)
    expires = make_token_expiration()
    access_token.expires = expires
    access_token.save()

def get_auth_token(user, client="GeoServer"):
    Application = get_application_model()
    app = Application.objects.get(name=client)
    access_token = AccessToken.objects.filter(user=user, application=app).order_by('-expires').first()
    return access_token


def get_auth_token_from_auth_header(auth_header):
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
