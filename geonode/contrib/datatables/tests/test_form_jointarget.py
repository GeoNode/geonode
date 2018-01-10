from django.utils import unittest
from geonode.contrib.datatables.forms import JoinTargetForm, ERR_MSG_START_YEAR_CANNOT_BE_GREATER, ERR_MSG_YEAR_TOO_HIGH


class JoinTargetTestCase(unittest.TestCase):
    def setUp(self):
        pass
        #self.lion = Animal.objects.create(name="lion", sound="roar")
        #self.cat = Animal.objects.create(name="cat", sound="meow")

    def test_no_params(self):
        d = {}
        f = JoinTargetForm(d)
        self.assertEqual(f.is_valid(), True)

    def test_years(self):

        # start year < 9999
        d = dict(start_year=2000)
        f = JoinTargetForm(d)
        self.assertEqual(f.is_valid(), True)

        # nope: start year > 9999
        d = dict(start_year=10000)
        f = JoinTargetForm(d)
        self.assertEqual(f.is_valid(), False)

        # nope: start year > 9999
        d = dict(start_year=20000)
        f = JoinTargetForm(d)
        self.assertEqual(f.is_valid(), False)

        self.assertEqual(f.errors.has_key('start_year'), True)
        self.assertEqual(f.errors.get('start_year'), [ERR_MSG_YEAR_TOO_HIGH])

        # start year is negative
        d = dict(start_year=-1)
        f = JoinTargetForm(d)
        self.assertEqual(f.is_valid(), True)

        # start_year < end_year
        d = dict(start_year=1989, end_year=2015)
        f = JoinTargetForm(d)
        self.assertEqual(f.is_valid(), True)

        # start_year = end_year
        d = dict(start_year=1989, end_year=1989)
        f = JoinTargetForm(d)
        self.assertEqual(f.is_valid(), True)

        # nope: start_year > end_year
        d = dict(start_year=1989, end_year=1981)
        f = JoinTargetForm(d)
        self.assertEqual(f.is_valid(), False)
        self.assertEqual(f.errors.has_key('__all__'), True)
        self.assertEqual(f.errors.get('__all__'), [ERR_MSG_START_YEAR_CANNOT_BE_GREATER])


    def test_error_messages(self):

        # start year < 9999
        d = dict(title='', start_year=10001, end_year=10000)
        f = JoinTargetForm(d)
        self.assertEqual(f.is_valid(), False)
        expected_str = 'end_year - %s<br />start_year - %s' % (ERR_MSG_YEAR_TOO_HIGH, ERR_MSG_YEAR_TOO_HIGH)
        self.assertEqual(f.get_error_messages_as_html_string(), expected_str)

        d = dict(title='', start_year=1979, end_year=1933)
        f = JoinTargetForm(d)
        self.assertEqual(f.is_valid(), False)
        self.assertEqual(f.get_error_messages_as_html_string(), ERR_MSG_START_YEAR_CANNOT_BE_GREATER)
