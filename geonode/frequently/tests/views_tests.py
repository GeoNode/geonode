"""
Tests for the models of the myapp application.

"""
from django.conf import settings
from django.core import mail
from django.test import TestCase

from django_libs.tests.mixins import ViewRequestFactoryTestMixin
from mixer.backend.django import mixer

from ..models import Entry, Feedback
from .. import views


class EntryPostMixin(ViewRequestFactoryTestMixin):
    """Mixin for Entry post scenarios."""
    def setUp(self):
        self.user = mixer.blend('auth.User')
        self.category_1 = mixer.blend('frequently.EntryCategory')
        self.category_2 = mixer.blend('frequently.EntryCategory')
        self.category_3 = mixer.blend('frequently.EntryCategory')
        self.entry_1 = mixer.blend('frequently.Entry', upvotes=2,
                                   published=True, amount_of_views=500)
        self.entry_1.category.add(self.category_1)
        self.entry_2 = mixer.blend('frequently.Entry', downvotes=4,
                                   published=True, amount_of_views=200)
        self.entry_2.category.add(self.category_1)
        self.entry_3 = mixer.blend('frequently.Entry', upvotes=3,
                                   published=True, amount_of_views=100)
        self.entry_3.category.add(self.category_1)
        self.entry_4 = mixer.blend('frequently.Entry', upvotes=7,
                                   published=True, amount_of_views=200)
        self.entry_4.category.add(self.category_2)
        self.entry_5 = mixer.blend('frequently.Entry', upvotes=2,
                                   published=True, amount_of_views=50)
        self.entry_5.category.add(self.category_2)

    def test_view(self):
        self.is_callable()

    def test_positive_feedback(self):
        data = {
            'up%d' % self.entry_1.pk: 'Foo',
            'user_id': self.user.pk
        }
        self.is_postable(user=self.user, data=data, add_session=True,
                         ajax=True)
        self.assertEqual(
            Entry.objects.get(pk=self.entry_1.pk).feedback_set.count(), 1)

    def test_negative_feedback(self):
        self.is_callable(self.user)
        data = {
            'down%d' % self.entry_1.pk: 'Foo',
            'user_id': self.user.pk
        }
        self.is_postable(user=self.user, data=data, add_session=True,
                         ajax=True)
        self.assertEqual(Feedback.objects.get(pk=1).validation, 'N')

    def test_positive_feedback_with_ajax(self):
        data = {
            'up%d' % self.entry_1.pk: 'Foo',
            'user_id': '55555'
        }
        self.is_postable(data=data, ajax=True, add_session=True)
        self.assertEqual(len(Entry.objects.get(
            pk=self.entry_1.pk).feedback_set.all()), 1)
        data = {
            'up%d' % self.entry_1.pk: 'Foo',
            'user_id': 'test'
        }
        self.is_postable(data=data, ajax=True, add_session=True)
        self.assertEqual(Entry.objects.get(
            pk=self.entry_1.pk).feedback_set.count(), 2)
        data = {
            'upXXX': 'Foo',
            'user_id': 'test',
        }
        self.is_not_callable(post=True, data=data, ajax=True, add_session=True)
        data = {
            'up999': 'Foo',
            'user_id': 'test',
        }
        self.is_not_callable(post=True, data=data, ajax=True, add_session=True)

    def test_negative_feedback_with_ajax(self):
        data = {
            'down%d' % self.entry_1.pk: 'Foo',
        }
        self.is_postable(data=data, ajax=True, add_session=True)
        self.assertEqual(Feedback.objects.get(pk=1).validation, 'N')

    def test_rating_refresh_ajax_request(self):
        data = {
            'rating_id': 'rating_id{}'.format(self.entry_1.pk),
        }
        resp = self.is_postable(data=data, ajax=True)
        self.assertEqual(int(resp.content), self.entry_1.rating())
        self.is_not_callable(post=True, data={'rating_id': 'rating_idXXX'},
                             ajax=True)
        self.is_not_callable(post=True, data={'rating_id': 'rating_id999'},
                             ajax=True)

    def test_feedback_submission_with_ajax(self):
        feedback = mixer.blend('frequently.Feedback')
        remark = 'Your app is beautiful'
        data = {
            'feedback%d' % feedback.pk: True,
            'remark': remark,
        }
        self.is_postable(data=data, ajax=True)
        self.assertEqual(Feedback.objects.get(pk=feedback.pk).remark, remark)
        data = {
            'feedbackXXX': True,
            'remark': remark,
        }
        self.is_not_callable(post=True, data=data, ajax=True)
        data = {
            'feedback999': True,
            'remark': remark,
        }
        self.is_not_callable(post=True, data=data, ajax=True)
        self.is_postable(data={}, ajax=True)

    def test_last_view_date_with_ajax(self):
        data = {
            'get_answer': self.entry_1.pk,
        }
        self.is_postable(data=data, ajax=True)
        self.assertGreater(
            Entry.objects.get(pk=self.entry_1.pk).last_view_date,
            self.entry_1.last_view_date,
        )


class EntryCategoryListViewTestCase(EntryPostMixin, TestCase):
    """Tests for EntryCategoryListView view class."""
    view_class = views.EntryCategoryListView


class EntryDetailViewTestCase(EntryPostMixin, TestCase):
    """Tests for the ``EntryDetailView`` generic view class."""
    view_class = views.EntryDetailView

    def get_view_kwargs(self):
        return {'slug': self.entry_1.slug}


class EntryCreateViewTestCase(ViewRequestFactoryTestMixin, TestCase):
    """Tests for the ``EntryCreateView`` generic view class."""
    view_class = views.EntryCreateView

    def setUp(self):
        self.user = mixer.blend('auth.User')

    def test_view(self):
        self.is_callable(self.user)
        data = {
            'question': 'Foo',
            'submitted_by': 'info@example.com',
        }
        self.is_postable(user=self.user, data=data,
                         to_url_name='frequently_list')
        settings.FREQUENTLY_RECIPIENTS = (
            ('Your Name', 'info@example.com'),
        )
        self.is_postable(user=self.user, data=data,
                         to_url_name='frequently_list')
        self.assertEqual(len(mail.outbox), 1)
