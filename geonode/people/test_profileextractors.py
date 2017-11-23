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
            "email-address": "phony_mail",
            "first-name": "phony_first_name",
            "headline": "phony_headline",
            "last-name": "phony_last_name",
            "positions": {
                "position": {
                    "title": "phony_title",
                    "company": {
                        "name": "phony_company",
                    },
                }
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
        self.assertEqual(result, self.data["email-address"])

    def test_extract_fax(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_fax(self.data)

    def test_extract_first_name(self):
        result = self.extractor.extract_first_name(self.data)
        self.assertEqual(result, self.data["first-name"])

    def test_extract_last_name(self):
        result = self.extractor.extract_last_name(self.data)
        self.assertEqual(result, self.data["last-name"])

    def test_extract_organization(self):
        result = self.extractor.extract_organization(self.data)
        self.assertEqual(
            result, self.data["positions"]["position"]["company"]["name"])

    def test_extract_organization_no_positions(self):
        data = self.data.copy()
        del data["positions"]
        result = self.extractor.extract_organization(data)
        self.assertEqual(result, "")

    def test_extract_organization_no_positions_position(self):
        data = self.data.copy()
        del data["positions"]["position"]
        result = self.extractor.extract_organization(data)
        self.assertEqual(result, "")

    def test_extract_organization_no_positions_position_company(self):
        data = self.data.copy()
        del data["positions"]["position"]["company"]
        result = self.extractor.extract_organization(data)
        self.assertEqual(result, "")

    def test_extract_organization_no_positions_position_company_name(self):
        data = self.data.copy()
        del data["positions"]["position"]["company"]["name"]
        result = self.extractor.extract_organization(data)
        self.assertEqual(result, "")

    def test_extract_position(self):
        result = self.extractor.extract_position(self.data)
        self.assertEqual(result, self.data["positions"]["position"]["title"])

    def test_extract_position_no_positions(self):
        data = self.data.copy()
        del data["positions"]
        result = self.extractor.extract_position(data)
        self.assertEqual(result, "")

    def test_extract_position_no_positions_position(self):
        data = self.data.copy()
        del data["positions"]["position"]
        result = self.extractor.extract_position(data)
        self.assertEqual(result, "")

    def test_extract_position_no_positions_position_title(self):
        data = self.data.copy()
        del data["positions"]["position"]["title"]
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
