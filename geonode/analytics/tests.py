from django.test import TestCase
from django.test.client import Client

class AnalyticsTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_analytics_tab(self):
        response = self.client.get('/analytics/')
        self.assertEqual(response.status_code, 200)

    def test_new_analysis(self):
        response = self.client.get('/analytics/new/')
        self.assertEqual(response.status_code, 200)
