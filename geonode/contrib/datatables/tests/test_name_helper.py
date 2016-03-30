from django.utils import unittest
from geonode.contrib.datatables.name_helper import get_unique_viewname,\
                                        standardize_table_name,\
                                        get_random_chars

class JoinTargetTestCase(unittest.TestCase):
    def setUp(self):
        pass
        #self.lion = Animal.objects.create(name="lion", sound="roar")
        #self.cat = Animal.objects.create(name="cat", sound="meow")

    def test_name_starts_with_digit(self):

        tname = standardize_table_name('12345')
        self.assertEqual(tname, 't_12345')

        # digit + truncate
        tname = standardize_table_name('45no_di_it_start')
        self.assertEqual(tname, 't_45no_di_i')

    def test_name_is_slugified(self):

        tname = standardize_table_name('hello" there-table')
        self.assertEqual(tname, 'hello_there')

        tname = standardize_table_name('1-2-button-+shoe')
        self.assertEqual(tname, 't_1_2_butto')

    def test_random_chars(self):

        tname = 'mytable'
        for x in range(1, 11):
            random_chars = get_random_chars(x+1)
            new_name = '{0}_{1}'.format(tname, random_chars)
            self.assertEqual(len(new_name), len(tname) + x + 2)
