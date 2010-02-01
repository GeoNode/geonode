from django.test import TestCase
from django.template import Context, Template, TemplateSyntaxError

class CoreTemplateTestCase(TestCase):
    def test_media_good(self):
        ctx = Context()
        tpl = Template("""{% load geonode_media %}{% geonode_media "ext_base" %}""")
        self.assertEquals("http://extjs.cachefly.net/ext-3.0.0/", tpl.render(ctx))

    def test_media_bad(self):
        try:
            ctx = Context()
            tpl = Template("""{% load geonode_media %}{% geonode_media "foobarbaz" %}""")
            tpl.render(ctx)
            self.fail()
        except TemplateSyntaxError:
            pass
