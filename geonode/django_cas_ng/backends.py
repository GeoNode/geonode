"""CAS authentication backend"""
from __future__ import absolute_import
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.conf import settings

from django_cas_ng.signals import cas_user_authenticated
from .utils import get_cas_client

User = get_user_model()

__all__ = ['CASBackend']


class CASBackend(ModelBackend):
    """CAS authentication backend"""

    def authenticate(self, ticket, service, request):
        """Verifies CAS ticket and gets or creates User object"""
        client = get_cas_client(service_url=service)
        username, attributes, pgtiou = client.verify_ticket(ticket)
        if attributes:
            request.session['attributes'] = attributes
        if not username:
            return None

        username_case = settings.CAS_FORCE_CHANGE_USERNAME_CASE
        if username_case == 'lower':
            username = username.lower()
        elif username_case == 'upper':
            username = username.upper()

        try:
            user = User.objects.get(**{User.USERNAME_FIELD: username})
            created = False
        except User.DoesNotExist:
            # check if we want to create new users, if we don't fail auth
            if not settings.CAS_CREATE_USER:
                return None
            # user will have an "unusable" password
            user = User.objects.create_user(username, '')
            user.save()
            created = True

        if pgtiou and settings.CAS_PROXY_CALLBACK:
            request.session['pgtiou'] = pgtiou

        # send the `cas_user_authenticated` signal
        cas_user_authenticated.send(
            sender=self,
            user=user,
            created=created,
            attributes=attributes,
            ticket=ticket,
            service=service,
        )
        return user

    def get_user(self, user_id):
        """Retrieve the user's entry in the User model if it exists"""

        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
