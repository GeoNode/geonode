"""Tests for the forms of the ``django-frequently`` app."""
from django.test import TestCase

from mixer.backend.django import mixer

from .. import forms


class EntryFormTestCase(TestCase):
    """Tests for the ``EntryForm`` form class."""
    def setUp(self):
        self.owner = mixer.blend('auth.User')

    def test_form(self):
        data = {
            'question': ('This is a very long question to test the slug'
                         ' generator and the truncation results. Sometimes'
                         ' questions can become very very long, so we will'
                         ' have to be careful to not create exceptions.'),
            'submitted_by': 'info@example.com',
        }
        form = forms.EntryForm(data=data)
        self.assertTrue(form.is_valid())

        with self.settings(FREQUENTLY_REQUIRE_EMAIL=False):
            form = forms.EntryForm(data=data, owner=self.owner)
            self.assertTrue(form.is_valid())

            obj = form.save()
            self.assertEqual(obj.submitted_by, self.owner.email)
            self.assertEqual(obj.slug, ('this-is-a-very-long-question-to-test-'
                                        'the-slug-generator-and-the-truncation'
                                        '-results-sometimes-questio'))
