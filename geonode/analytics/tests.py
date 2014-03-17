from django.test import TestCase
from django.test.client import Client

class AnalyticsTest(TestCase):
    
    def setUp(self):
        self.client = Client()

    def test_analytics_tab(self):
        r = self.client.get('/analytics/')
        self.assertEqual(r.status_code, 200)

    def test_new_analysis(self):
        r = self.client.get('/analytics/new/')
        self.assertEqual(r.status_code, 200)
