"""
Tests for the models of the ``django-frequently`` app.

"""
from django.test import TestCase

from mixer.backend.django import mixer


class EntryCategoryTestCase(TestCase):
    """Tests for the ``EntryCategory`` model class."""
    def test_model(self):
        obj = mixer.blend('frequently.EntryCategory')
        self.assertTrue(str(obj))


class EntryTestCase(TestCase):
    """Tests for the ``Entry`` model class."""
    def test_model(self):
        obj = mixer.blend('frequently.Entry')
        self.assertTrue(str(obj))


class FeedbackTestCase(TestCase):
    """Tests for the ``Feedback`` model class."""
    def test_model(self):
        obj = mixer.blend('frequently.Feedback')
        self.assertTrue(str(obj))
