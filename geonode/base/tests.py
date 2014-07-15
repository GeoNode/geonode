from django.test import TestCase
from geonode.base.models import ResourceBase


class ThumbnailTests(TestCase):

    def setUp(self):
        self.rb = ResourceBase.objects.create()

    def tearDown(self):
        t = self.rb.thumbnail
        if t:
            t.delete()

    def test_initial_behavior(self):
        self.assertFalse(self.rb.has_thumbnail())
        missing = self.rb.get_thumbnail_url()
        self.assertEquals('/static/geonode/img/missing_thumb.png', missing)
