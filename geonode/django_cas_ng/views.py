"""CAS login/logout replacement views"""

from __future__ import absolute_import
from __future__ import unicode_literals

from django.utils.six.moves import urllib_parse
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import (
    logout as auth_logout,
    login as auth_login,
    authenticate
)
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods

from importlib import import_module

SessionStore = import_module(settings.SESSION_ENGINE).SessionStore

from datetime import timedelta

from .signals import cas_user_logout
from .models import ProxyGrantingTicket, SessionTicket
from .utils import (get_cas_client, get_service_url,
                    get_protocol, get_redirect_url,
                    get_user_from_session)

__all__ = ['login', 'logout', 'callback']


@csrf_exempt
@require_http_methods(["GET", "POST"])
def login(request, next_page=None, required=False):
    """Forwards to CAS login URL or verifies CAS ticket"""
    service_url = get_service_url(request, next_page)
    client = get_cas_client(service_url=service_url)

    if not next_page:
        next_page = get_redirect_url(request)

    if request.method == 'POST' and request.POST.get('logoutRequest'):
        clean_sessions(client, request)
        return HttpResponseRedirect(next_page)

    if request.user.is_authenticated():
        if settings.CAS_LOGGED_MSG is not None:
            message = settings.CAS_LOGGED_MSG % request.user.get_username()
            messages.success(request, message)
        return HttpResponseRedirect(next_page)

    ticket = request.GET.get('ticket')
    if ticket:
        user = authenticate(ticket=ticket,
                            service=service_url,
                            request=request)
        pgtiou = request.session.get("pgtiou")
        if user is not None:
            auth_login(request, user)
            if not request.session.exists(request.session.session_key):
                request.session.create()
            SessionTicket.objects.create(
                session_key=request.session.session_key,
                ticket=ticket
            )

            if pgtiou and settings.CAS_PROXY_CALLBACK:
                # Delete old PGT
                ProxyGrantingTicket.objects.filter(
                    user=user,
                    session_key=request.session.session_key
                ).delete()
                # Set new PGT ticket
                try:
                    pgt = ProxyGrantingTicket.objects.get(pgtiou=pgtiou)
                    pgt.user = user
                    pgt.session_key = request.session.session_key
                    pgt.save()
                except ProxyGrantingTicket.DoesNotExist:
                    pass

            if settings.CAS_LOGIN_MSG is not None:
                name = user.get_username()
                message = settings.CAS_LOGIN_MSG % name
                messages.success(request, message)
            return HttpResponseRedirect(next_page)
        elif settings.CAS_RETRY_LOGIN or required:
            return HttpResponseRedirect(client.get_login_url())
        else:
            error = "<h1>{0}</h1><p>{1}</p>".format(_('Forbidden'), _('Login failed.'))
            return HttpResponseForbidden(error)
    else:
        return HttpResponseRedirect(client.get_login_url())


@require_http_methods(["GET"])
def logout(request, next_page=None):
    """Redirects to CAS logout page"""
    # try to find the ticket matching current session for logout signal
    try:
        st = SessionTicket.objects.get(session_key=request.session.session_key)
        ticket = st.ticket
    except SessionTicket.DoesNotExist:
        ticket = None
    # send logout signal
    cas_user_logout.send(
        sender="manual",
        user=request.user,
        session=request.session,
        ticket=ticket,
    )
    auth_logout(request)
    # clean current session ProxyGrantingTicket and SessionTicket
    ProxyGrantingTicket.objects.filter(session_key=request.session.session_key).delete()
    SessionTicket.objects.filter(session_key=request.session.session_key).delete()
    next_page = next_page or get_redirect_url(request)
    if settings.CAS_LOGOUT_COMPLETELY:
        protocol = get_protocol(request)
        host = request.get_host()
        redirect_url = urllib_parse.urlunparse(
            (protocol, host, next_page, '', '', ''),
        )
        client = get_cas_client()
        return HttpResponseRedirect(client.get_logout_url(redirect_url))
    else:
        # This is in most cases pointless if not CAS_RENEW is set. The user will
        # simply be logged in again on next request requiring authorization.
        return HttpResponseRedirect(next_page)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def callback(request):
    """Read PGT and PGTIOU sent by CAS"""
    if request.method == 'POST' and request.POST.get('logoutRequest'):
        clean_sessions(get_cas_client(), request)
        return HttpResponse("{0}\n".format(_('ok')), content_type="text/plain")
    elif request.method == 'GET':
        pgtid = request.GET.get('pgtId')
        pgtiou = request.GET.get('pgtIou')
        pgt = ProxyGrantingTicket.objects.create(pgtiou=pgtiou, pgt=pgtid)
        pgt.save()
        ProxyGrantingTicket.objects.filter(
            session_key=None,
            date__lt=(timezone.now() - timedelta(seconds=60))
        ).delete()
        return HttpResponse("{0}\n".format(_('ok')), content_type="text/plain")


def clean_sessions(client, request):
    for slo in client.get_saml_slos(request.POST.get('logoutRequest')):
        try:
            st = SessionTicket.objects.get(ticket=slo.text)
            session = SessionStore(session_key=st.session_key)
            # send logout signal
            cas_user_logout.send(
                sender="slo",
                user=get_user_from_session(session),
                session=session,
                ticket=slo.text,
            )
            session.flush()
            # clean logout session ProxyGrantingTicket and SessionTicket
            ProxyGrantingTicket.objects.filter(session_key=st.session_key).delete()
            SessionTicket.objects.filter(session_key=st.session_key).delete()
        except SessionTicket.DoesNotExist:
            pass
