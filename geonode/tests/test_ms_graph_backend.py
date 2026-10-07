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

import base64
from unittest import mock

import requests
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMessage, EmailMultiAlternatives
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
        # send_messages posts through a requests.Session() context manager.
        self.mock_post = self.mock_requests.Session.return_value.__enter__.return_value.post
        self.mock_post.return_value = _ok_response()

    def _backend(self, fail_silently=False):
        return MicrosoftGraphEmailBackend(fail_silently=fail_silently)

    def _last_payload(self):
        return self.mock_post.call_args.kwargs["json"]

    def _last_url(self):
        return self.mock_post.call_args.args[0]

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

    def test_missing_credentials_non_silent_raises(self):
        msg = EmailMessage("subj", "body", to=["a@example.com"])
        with self.settings(MICROSOFT_GRAPH_API_CREDENTIALS={}):
            with self.assertRaises(ImproperlyConfigured):
                self._backend(fail_silently=False).send_messages([msg])

    def test_save_to_sent_items_is_boolean(self):
        msg = EmailMessage("subj", "body", to=["a@example.com"])
        with self.settings(MICROSOFT_GRAPH_API_CREDENTIALS=VALID_CREDS):
            self._backend().send_messages([msg])
        self.assertIs(self._last_payload()["saveToSentItems"], True)

    def test_mail_from_display_name_is_stripped_in_url(self):
        creds = {**VALID_CREDS, "mail_from": "GeoNode <no-reply@geonode.org>"}
        msg = EmailMessage("subj", "body", to=["a@example.com"])
        with self.settings(MICROSOFT_GRAPH_API_CREDENTIALS=creds):
            self._backend().send_messages([msg])
        self.assertEqual(self._last_url(), GRAPH_SENDMAIL_ENDPOINT.format(mailbox="no-reply@geonode.org"))

    def test_html_alternative_is_sent_as_html(self):
        msg = EmailMultiAlternatives("subj", "plain body", to=["a@example.com"])
        msg.attach_alternative("<p>rich</p>", "text/html")
        with self.settings(MICROSOFT_GRAPH_API_CREDENTIALS=VALID_CREDS):
            self._backend().send_messages([msg])
        body = self._last_payload()["message"]["body"]
        self.assertEqual(body["contentType"], "HTML")
        self.assertEqual(body["content"], "<p>rich</p>")

    def test_extra_headers_forwarded(self):
        msg = EmailMessage("subj", "body", to=["a@example.com"], headers={"X-Custom": "value"})
        with self.settings(MICROSOFT_GRAPH_API_CREDENTIALS=VALID_CREDS):
            self._backend().send_messages([msg])
        self.assertIn(
            {"name": "X-Custom", "value": "value"},
            self._last_payload()["message"]["internetMessageHeaders"],
        )

    def test_attachment_is_base64_encoded(self):
        msg = EmailMessage("subj", "body", to=["a@example.com"])
        msg.attach("report.csv", "a,b,c", "text/csv")
        with self.settings(MICROSOFT_GRAPH_API_CREDENTIALS=VALID_CREDS):
            self._backend().send_messages([msg])
        attachments = self._last_payload()["message"]["attachments"]
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0]["@odata.type"], "#microsoft.graph.fileAttachment")
        self.assertEqual(attachments[0]["name"], "report.csv")
        self.assertEqual(attachments[0]["contentType"], "text/csv")
        self.assertEqual(base64.b64decode(attachments[0]["contentBytes"]).decode("utf-8"), "a,b,c")
