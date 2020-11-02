"""Tests for the tags of the ``frequently`` app."""
from django.test import TestCase

from mixer.backend.django import mixer

from ..templatetags.frequently_tags import render_category


class RenderCategoryTestCase(TestCase):
    """Tests for the ``render_category`` tag."""
    longMessage = True

    def setUp(self):
        self.category = mixer.blend('frequently.EntryCategory')

    def test_tag(self):
        self.assertEqual(render_category(self.category.slug),
                         {'category': self.category},
                         msg=('Returns category, if slug is found.'))

        self.assertEqual(render_category('foo'), {}, msg=(
            'Returns empty context, if category does not exist.'))
