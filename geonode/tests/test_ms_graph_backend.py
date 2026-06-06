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

from unittest import mock

import requests
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMessage
from django.test import SimpleTestCase

from geonode.email_backends.ms_graph_backend import (
    GRAPH_SENDMAIL_ENDPOINT,
    MicrosoftGraphEmailBackend,
)

VALID_CREDS = {
    "tenant_id": "tenant-xyz",
    "client_id": "client-xyz",
    "client_secret": "secret-xyz",
    "mail_from": "noreply@example.com",
}


def _ok_response():
    resp = mock.Mock(spec=requests.Response)
    resp.ok = True
    resp.status_code = 202
    resp.text = ""
    return resp


class MicrosoftGraphEmailBackendTests(SimpleTestCase):
    def setUp(self):
        self.msal_patch = mock.patch("geonode.email_backends.ms_graph_backend.msal")
        self.requests_patch = mock.patch("geonode.email_backends.ms_graph_backend.requests")
        self.mock_msal = self.msal_patch.start()
        self.mock_requests = self.requests_patch.start()
        self.addCleanup(self.msal_patch.stop)
        self.addCleanup(self.requests_patch.stop)

        self.mock_app = mock.Mock()
        self.mock_msal.ConfidentialClientApplication.return_value = self.mock_app
        self.mock_app.acquire_token_silent.return_value = None
        self.mock_app.acquire_token_for_client.return_value = {"access_token": "tok"}
        self.mock_requests.post.return_value = _ok_response()

    def _backend(self, fail_silently=False):
        return MicrosoftGraphEmailBackend(fail_silently=fail_silently)

    def _last_payload(self):
        return self.mock_requests.post.call_args.kwargs["json"]

    def _last_url(self):
        return self.mock_requests.post.call_args.args[0]

    def test_html_body_marked_as_html(self):
        msg = EmailMessage("subj", "<p>hi</p>", to=["a@example.com"])
        msg.content_subtype = "html"
        with self.settings(MICROSOFT_GRAPH_API_CREDENTIALS=VALID_CREDS):
            self.assertEqual(self._backend().send_messages([msg]), 1)
        payload = self._last_payload()
        self.assertEqual(payload["message"]["body"]["contentType"], "HTML")
        self.assertEqual(payload["message"]["body"]["content"], "<p>hi</p>")

    def test_plain_body_marked_as_text(self):
        msg = EmailMessage("subj", "line1\nline2", to=["a@example.com"])
        with self.settings(MICROSOFT_GRAPH_API_CREDENTIALS=VALID_CREDS):
            self.assertEqual(self._backend().send_messages([msg]), 1)
        self.assertEqual(self._last_payload()["message"]["body"]["contentType"], "Text")

    def test_to_cc_bcc_forwarded(self):
        msg = EmailMessage(
            "subj",
            "body",
            to=["a@example.com", "b@example.com"],
            cc=["c@example.com"],
            bcc=["d@example.com"],
        )
        with self.settings(MICROSOFT_GRAPH_API_CREDENTIALS=VALID_CREDS):
            self.assertEqual(self._backend().send_messages([msg]), 1)
        payload = self._last_payload()["message"]
        self.assertEqual(
            [r["emailAddress"]["address"] for r in payload["toRecipients"]],
            ["a@example.com", "b@example.com"],
        )
        self.assertEqual([r["emailAddress"]["address"] for r in payload["ccRecipients"]], ["c@example.com"])
        self.assertEqual([r["emailAddress"]["address"] for r in payload["bccRecipients"]], ["d@example.com"])

    def test_reply_to_forwarded(self):
        msg = EmailMessage("subj", "body", to=["a@example.com"], reply_to=["replies@example.com"])
        with self.settings(MICROSOFT_GRAPH_API_CREDENTIALS=VALID_CREDS):
            self._backend().send_messages([msg])
        self.assertEqual(
            self._last_payload()["message"]["replyTo"],
            [{"emailAddress": {"address": "replies@example.com"}}],
        )

    def test_url_uses_configured_mail_from(self):
        msg = EmailMessage("subj", "body", from_email="other@example.com", to=["a@example.com"])
        with self.settings(MICROSOFT_GRAPH_API_CREDENTIALS=VALID_CREDS):
            self._backend().send_messages([msg])
        self.assertEqual(self._last_url(), GRAPH_SENDMAIL_ENDPOINT.format(mailbox=VALID_CREDS["mail_from"]))

    def test_token_acquired_once_per_send_messages_call(self):
        msgs = [EmailMessage("s", "b", to=["a@example.com"]) for _ in range(3)]
        with self.settings(MICROSOFT_GRAPH_API_CREDENTIALS=VALID_CREDS):
            self.assertEqual(self._backend().send_messages(msgs), 3)
        # MSAL client constructed once; token acquired once across 3 sends.
        self.assertEqual(self.mock_msal.ConfidentialClientApplication.call_count, 1)
        self.assertEqual(self.mock_app.acquire_token_for_client.call_count, 1)
        self.assertEqual(self.mock_requests.post.call_count, 3)

    def test_missing_credentials_non_silent_raises(self):
        msg = EmailMessage("subj", "body", to=["a@example.com"])
        with self.settings(MICROSOFT_GRAPH_API_CREDENTIALS={}):
            with self.assertRaises(ImproperlyConfigured):
                self._backend(fail_silently=False).send_messages([msg])