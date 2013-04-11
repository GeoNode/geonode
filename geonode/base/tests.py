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

    def test_saving(self):
        # monkey patch our render function to just put the 'spec' into the file
        self.rb._render_thumbnail = lambda *a, **kw: '%s' % a[0]

        self._do_save_test('abc', 1)
        self._do_save_test('xyz', 2)

    def _do_save_test(self, content, version):
        self.rb.save_thumbnail(content)
        thumb = self.rb.thumbnail
        self.assertEquals(version, thumb.version)
        self.assertEqual(content, thumb.thumb_file.read())
        self.assertEqual(content, thumb.thumb_spec)
