"""unit tests for geonode.people.profileextractors"""

from unittest import TestCase

from geonode.people import profileextractors


class FacebookExtractorTestCase(TestCase):

    def setUp(self):
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


class LinkedInExtractorTestCase(TestCase):

    def setUp(self):
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
