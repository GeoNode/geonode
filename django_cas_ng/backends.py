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

from pprint import pprint

class CASBackend(ModelBackend):
    """CAS authentication backend"""

    def authenticate(self, ticket, service, request):
        """Verifies CAS ticket and gets or creates User object"""
        user = None
        client = get_cas_client(service_url=service)
        username, attributes, pgtiou = client.verify_ticket(ticket)
        if attributes:
            request.session['attributes'] = attributes
        if not username:
            pprint("no username found")
            return None

        username_case = settings.CAS_FORCE_CHANGE_USERNAME_CASE
        if username_case == 'lower':
            username = username.lower()
        elif username_case == 'upper':
            username = username.upper()

        try:
            pprint("checking if user is present")
            user = User.objects.get(**{User.USERNAME_FIELD: username})
            created = False
        except User.DoesNotExist:
            # check if we want to create new users, if we don't fail auth
            pprint("I am here")
            if not settings.CAS_CREATE_USER:
                pprint("I am here again")
                return None
            # user will have an "unusable" password
            pprint("I am here once more")
            user = User.objects.create_user(username, '')
            user.save()
            created = True
        
        if not user:
            pprint("user variable is empty")
            
        pprint(str(user.is_superuser))
        
        if attributes and user:
            setattr(user, "email", attributes["email"])
            setattr(user, "first_name",attributes["first_name"])
            setattr(user, "last_name", attributes["last_name"])
            setattr(user,"is_active",attributes["is_active"])
            setattr(user,"is_superuser", attributes["is_superuser"])
            #pprint(attributes["is_superuser"])
            #pprint(user.is_superuser)
            setattr(user,"is_staff", attributes["is_staff"])
            user.save()

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

@receive(cas_user_authenticated)
def handle_user_authenticated(sender, **kwargs):
    user = kwargs.get("user")
    attributes = kwargs.get("attributes")
    pprint('User.is_superuser:'+ str(user.is_superuser))
    pprint("atrributes: "+str(attributes))
