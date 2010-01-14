"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""
from django.test.client import Client
import unittest

class SimpleTest(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def test_api(self):
        response = self.client.get('/safehospitals/')
        self.failUnlessEqual(response.status_code,200)
