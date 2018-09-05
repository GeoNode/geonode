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

from geonode.tests.base import GeoNodeBaseTestSupport

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.core import mail
from django.contrib.sites.models import Site

from geonode.people import profileextractors


class PeopleTest(GeoNodeBaseTestSupport):

    fixtures = ['initial_data.json', 'people_data.json']

    def test_forgot_username(self):
        url = reverse('forgot_username')

        # page renders
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

        # and responds for a bad email
        response = self.client.post(url, data={
            'email': 'foobar@doesnotexist.com'
        })
        self.assertContains(response, "No user could be found with that email address.")

        default_contact = get_user_model().objects.get(username='default_contact')
        response = self.client.post(url, data={
            'email': default_contact.email
        })
        # and sends a mail for a good one
        self.assertEqual(len(mail.outbox), 1)

        site = Site.objects.get_current()

        # Verify that the subject of the first message is correct.
        self.assertEqual(
            mail.outbox[0].subject,
            "Your username for " +
            site.name)


class FacebookExtractorTestCase(GeoNodeBaseTestSupport):

    def setUp(self):
        super(FacebookExtractorTestCase, self).setUp()
        self.data = {
            "email": "phony_mail",
            "first_name": "phony_first_name",
            "last_name": "phony_last_name",
            "cover": "phony_cover",
        }
        self.extractor = profileextractors.FacebookExtractor()

    def test_extract_area(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_area(self.data)

    def test_extract_city(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_city(self.data)

    def test_extract_country(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_country(self.data)

    def test_extract_delivery(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_delivery(self.data)

    def test_extract_email(self):
        result = self.extractor.extract_email(self.data)
        self.assertEqual(result, self.data["email"])

    def test_extract_fax(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_fax(self.data)

    def test_extract_first_name(self):
        result = self.extractor.extract_first_name(self.data)
        self.assertEqual(result, self.data["first_name"])

    def test_extract_last_name(self):
        result = self.extractor.extract_last_name(self.data)
        self.assertEqual(result, self.data["last_name"])

    def test_extract_organization(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_organization(self.data)

    def test_extract_position(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_position(self.data)

    def test_extract_profile(self):
        result = self.extractor.extract_profile(self.data)
        self.assertEqual(result, self.data["cover"])

    def test_extract_voice(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_voice(self.data)

    def test_extract_zipcode(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_zipcode(self.data)


class LinkedInExtractorTestCase(GeoNodeBaseTestSupport):

    def setUp(self):
        super(LinkedInExtractorTestCase, self).setUp()

        self.data = {
            "emailAddress": "phony_mail",
            "firstName": "phony_first_name",
            "headline": "phony_headline",
            "lastName": "phony_last_name",
            "positions": {
                "_total": 1,
                "values": [
                    {
                        "startDate": {},
                        "title": "some_title",
                        "company": {
                            "industry": "some_industry",
                            "size": "a_size",
                            "type": "some_type",
                            "id": 1,
                            "name": "phony_name"
                        },
                    }
                ],
            },
            "summary": "phony_summary",
        }
        self.extractor = profileextractors.LinkedInExtractor()

    def test_extract_area(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_area(self.data)

    def test_extract_city(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_city(self.data)

    def test_extract_country(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_country(self.data)

    def test_extract_delivery(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_delivery(self.data)

    def test_extract_email(self):
        result = self.extractor.extract_email(self.data)
        self.assertEqual(result, self.data["emailAddress"])

    def test_extract_fax(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_fax(self.data)

    def test_extract_first_name(self):
        result = self.extractor.extract_first_name(self.data)
        self.assertEqual(result, self.data["firstName"])

    def test_extract_last_name(self):
        result = self.extractor.extract_last_name(self.data)
        self.assertEqual(result, self.data["lastName"])

    def test_extract_organization(self):
        result = self.extractor.extract_organization(self.data)
        self.assertEqual(
            result, self.data["positions"]["values"][0]["company"]["name"])

    def test_extract_organization_no_positions(self):
        data = self.data.copy()
        del data["positions"]
        result = self.extractor.extract_organization(data)
        self.assertEqual(result, "")

    def test_extract_organization_no_positions_position_company(self):
        data = self.data.copy()
        del data["positions"]["values"][0]["company"]
        result = self.extractor.extract_organization(data)
        self.assertEqual(result, "")

    def test_extract_organization_no_positions_position_company_name(self):
        data = self.data.copy()
        del data["positions"]["values"][0]["company"]["name"]
        result = self.extractor.extract_organization(data)
        self.assertEqual(result, "")

    def test_extract_position(self):
        result = self.extractor.extract_position(self.data)
        self.assertEqual(
            result, self.data["positions"]["values"][0]["title"])

    def test_extract_position_no_positions(self):
        data = self.data.copy()
        del data["positions"]
        result = self.extractor.extract_position(data)
        self.assertEqual(result, "")

    def test_extract_position_no_positions_position_title(self):
        data = self.data.copy()
        del data["positions"]["values"][0]["title"]
        result = self.extractor.extract_position(data)
        self.assertEqual(result, "")

    def test_extract_profile(self):
        result = self.extractor.extract_profile(self.data)
        self.assertEqual(
            result, "\n".join(
                (self.data["headline"], self.data["summary"]))
        )

    def test_extract_profile_no_headline(self):
        data = self.data.copy()
        del data["headline"]
        result = self.extractor.extract_profile(data)
        self.assertEqual(result, data["summary"])

    def test_extract_profile_no_summary(self):
        data = self.data.copy()
        del data["summary"]
        result = self.extractor.extract_profile(data)
        self.assertEqual(result, data["headline"])

    def test_extract_profile_no_headline_and_no_summary(self):
        data = self.data.copy()
        del data["summary"]
        del data["headline"]
        result = self.extractor.extract_profile(data)
        self.assertEqual(result, "")

    def test_extract_voice(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_voice(self.data)

    def test_extract_zipcode(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_zipcode(self.data)
