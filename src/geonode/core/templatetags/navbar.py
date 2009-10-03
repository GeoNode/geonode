"""
Tag for rendering a context sensitive and extendable navigation
"""
from geonode.utils import SectionConfigMap
from django import template
from django.template import loader
from django.template.defaulttags import url
from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext
from geonode.utils import path_extrapolate


register = template.Library()


@register.tag('navbar')
def do_navbar(parser, token):
    """
    token is the page for the template

    @@ can we get a path or some route info?
    """
    try:
        tagname, whatpage = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, _("%r tag requires a single argument (what page should be selected in the nav?)" % token.contents.split()[0])
    return NavBar(whatpage, parser)


def load_navbar_config():
    fn = path_extrapolate('geonode/core/templatetags/navbar.ini')
    try:
        from django import settings
        newfn = getattr(settings, 'NAVBAR_INI', fn)
        if newfn is not None:
            fn = newfn
    except ImportError:
        pass
    
    #@@ cascade?
    conf = SectionConfigMap.load(fn)
    meta = conf['meta']
    # load defaults
    for section in conf.keys():
        cur = conf[section]
        for key in 'id','class',:
            if not cur.has_key(key):
                cur[key] = meta['default_' + key]
        conf[section] = cur
    return conf


class NavBar(template.Node):
    """
    Renderer for the nav bar
    """
    
    config = load_navbar_config()
    
    def __init__(self, whereami, parser):
        self.whereami = whereami
        self.parser = parser

    def get_url_node(self, spec):
        token = template.Token(template.TOKEN_BLOCK, "url %s" %spec)
        return url(self.parser, token)
     

    def compile_sections(self, context):
        sections = list()
        for section in self.visible:
            sect_info = self.config[section]
            if section == self.whereami:
                oldclass = sect_info['class']
                sect_info['class'] = "%s %s" %(oldclass, self.meta['active_class'])
            if sect_info['id'].startswith('%s'):
                sect_info['id'] = sect_info['id'] %section
            sect_info['url'] = self.get_url_node(sect_info['url']).render(context)
            sections.append(sect_info)
        return sections
    
    def render(self, context):
        #@@ cache this? doesn't change much
        sections = self.compile_sections(context)
        info = dict(active=self.whereami,
                    sections=sections,
                    config=self.config)
        return loader.render_to_string('navbar.html', info)

    @property
    def meta(self):
        return self.config['meta']

    @property
    def visible(self):
        return self.meta['visible'].split()






