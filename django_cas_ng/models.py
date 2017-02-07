# ⁻*- coding: utf-8 -*-
from django.db import models
from django.conf import settings
from .utils import (get_cas_client, get_service_url, get_user_from_session)


from importlib import import_module
from cas import CASError

SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


class ProxyError(ValueError):
    pass


class ProxyGrantingTicket(models.Model):
    class Meta:
        unique_together = ('session_key', 'user')
    session_key = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="+",
        null=True,
        blank=True
    )
    pgtiou = models.CharField(max_length=255, null=True, blank=True)
    pgt = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    @classmethod
    def clean_deleted_sessions(cls):
        for pgt in cls.objects.all():
            session = SessionStore(session_key=pgt.session_key)
            user = get_user_from_session(session)
            if not user.is_authenticated():
                pgt.delete()

    @classmethod
    def retrieve_pt(cls, request, service):
        """`request` should be the current HttpRequest object
        `service` a string representing the service for witch we want to
        retrieve a ticket.
        The function return a Proxy Ticket or raise `ProxyError`
        """
        try:
            pgt = cls.objects.get(user=request.user, session_key=request.session.session_key).pgt
        except cls.DoesNotExist:
            raise ProxyError(
                "INVALID_TICKET",
                "No proxy ticket found for this HttpRequest object"
            )
        else:
            service_url = get_service_url(request)
            client = get_cas_client(service_url=service_url)
            try:
                return client.get_proxy_ticket(pgt, service)
            # change CASError to ProxyError nicely
            except CASError as error:
                raise ProxyError(*error.args)
            # juste embed other errors
            except Exception as e:
                raise ProxyError(e)


class SessionTicket(models.Model):
    session_key = models.CharField(max_length=255)
    ticket = models.CharField(max_length=255)

    @classmethod
    def clean_deleted_sessions(cls):
        for st in cls.objects.all():
            session = SessionStore(session_key=st.session_key)
            user = get_user_from_session(session)
            if not user.is_authenticated():
                st.delete()
