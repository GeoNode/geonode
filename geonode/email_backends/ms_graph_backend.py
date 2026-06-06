# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2026 Open Source Geospatial Foundation - all rights reserved
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
"""Django email backend that sends mail through Microsoft 365.

Uses the Microsoft Graph ``sendMail`` API over the OAuth2 client-credentials
flow (application permissions) against an Azure AD app registration that holds
the ``Mail.Send`` application permission. The mailbox named by
``MICROSOFT_GRAPH_API_CREDENTIALS['mail_from']`` is always used as the sender;
the display name shown to recipients comes from that mailbox's Azure AD
configuration.

Known limitations: ``EmailMultiAlternatives`` (HTML + plain-text bodies) is sent
as a single body using ``content_subtype``; attachments and ``extra_headers``
are not forwarded to Graph.
"""

import logging

import msal
import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

GRAPH_TOKEN_SCOPE = ["https://graph.microsoft.com/.default"]
GRAPH_SENDMAIL_ENDPOINT = "https://graph.microsoft.com/v1.0/users/{mailbox}/sendMail"
GRAPH_REQUEST_TIMEOUT = 30  # seconds; requests.post would otherwise wait forever


class MicrosoftGraphEmailBackend(BaseEmailBackend):
    """
    Send Django EmailMessages through Microsoft 365 via the Graph API.
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self._msal_app = None

    def _get_access_token(self):
        """
        Return ``(creds, token)`` or raise. Validates settings and acquires a Graph token.
        """
        creds = getattr(settings, "MICROSOFT_GRAPH_API_CREDENTIALS", {}) or {}
        missing = [k for k in ("tenant_id", "client_id", "client_secret", "mail_from") if not creds.get(k)]
        if missing:
            raise ImproperlyConfigured(f"MICROSOFT_GRAPH_API_CREDENTIALS is missing required keys: {missing}")

        if self._msal_app is None:
            self._msal_app = msal.ConfidentialClientApplication(
                client_id=creds["client_id"],
                client_credential=creds["client_secret"],
                authority=f"https://login.microsoftonline.com/{creds['tenant_id']}",
                token_cache=msal.SerializableTokenCache(),
            )

        result = self._msal_app.acquire_token_silent(
            GRAPH_TOKEN_SCOPE, account=None
        ) or self._msal_app.acquire_token_for_client(scopes=GRAPH_TOKEN_SCOPE)
        token = (result or {}).get("access_token")
        if not token:
            error = (result or {}).get("error_description", "no result from MSAL")
            raise RuntimeError(f"Microsoft Graph token acquisition failed: {error}")
        return creds, token

    def send_messages(self, email_messages):
        """
        Send multiple email messages using Microsoft Graph API.
        """
        if not email_messages:
            return 0
        try:
            creds, token = self._get_access_token()
        except Exception:
            if not self.fail_silently:
                raise
            logger.exception("Microsoft Graph token acquisition failed")
            return 0

        sent = 0
        for message in email_messages:
            try:
                self._send(message, token, creds)
                sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
                logger.exception("Microsoft Graph sendMail failed for %s", message.to)
        return sent

    def _send(self, message, token, creds):
        """
        Send a single email using Microsoft Graph API.
        """
        content_type = "HTML" if getattr(message, "content_subtype", "plain") == "html" else "Text"
        payload = {
            "message": {
                "subject": message.subject,
                "body": {"contentType": content_type, "content": message.body},
                "toRecipients": [{"emailAddress": {"address": addr}} for addr in message.to],
                "ccRecipients": [{"emailAddress": {"address": addr}} for addr in message.cc],
                "bccRecipients": [{"emailAddress": {"address": addr}} for addr in message.bcc],
            },
            "saveToSentItems": "true",
        }
        if message.reply_to:
            payload["message"]["replyTo"] = [{"emailAddress": {"address": addr}} for addr in message.reply_to]

        response = requests.post(
            GRAPH_SENDMAIL_ENDPOINT.format(mailbox=creds["mail_from"]),
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=GRAPH_REQUEST_TIMEOUT,
        )
        if not response.ok:
            raise RuntimeError(f"Microsoft Graph sendMail returned HTTP {response.status_code}: {response.text}")
        logger.info("Microsoft Graph email sent to %s", message.to)
