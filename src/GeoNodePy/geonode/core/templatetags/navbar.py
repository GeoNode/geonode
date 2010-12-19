"""
Tag for rendering a context sensitive and extendable navigation
"""
import os
from pprint import pformat
from django import template
from django.template import loader
from django.template.defaulttags import url
from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext
from geonode.utils import ConfigMap, DictMixin


register = template.Library()

DEFAULT_PATH = 'geonode/core/templatetags/navbar.ini'
DEFAULT_TEMPLATE = 'navbar.html'

@register.tag('navbar')
def do_navbar(parser, token, template=DEFAULT_TEMPLATE):
    """
    token is the page for the template

    @@ can we get a path or some route info?
    """
    spec = token.split_contents()
    if len(spec) == 2:
        tagname, whatpage = spec
    elif len(spec) == 3:
        tagname, whatpage, template = spec
    else:
        raise template.TemplateSyntaxError, _("%r tag requires a single argument (what page should be selected in the nav?)" % token.contents.split()[0])
    return NavBar(whatpage, parser, template)


def prep_config(mapping):
    meta = mapping['meta']
    # load defaults
    for section in mapping.keys():
        cur = mapping[section]
        for key in 'id','item_class', 'link_class':
            if not cur.has_key(key):
                cur[key] = meta['default_' + key]
        mapping[section] = cur
    return mapping

    
def load_navbar_config(path=DEFAULT_PATH):
    try:
        from django.conf import settings
        conf = settings.NAVBAR
    except ImportError:
        conf = os.path.join(settings.PROJECT_ROOT, path)

    if isinstance(conf, basestring):
        conf = dict(ConfigMap.load(conf))

    return prep_config(conf)


class NavBar(template.Node):
    """
    Renderer for the nav bar
    """
    
    config = load_navbar_config()
    
    def __init__(self, whereami, parser, template):
        self.whereami = whereami
        self.parser = parser
        self.template = template

    def get_url_node(self, spec):
        token = template.Token(template.TOKEN_BLOCK, "url %s" %spec)
        return url(self.parser, token)

    def compile_sections(self, context):
        sections = list()
        for section in self.visible:
            # copy the section dict to protect against accidental
            # writes
            sect_info = dict(self.config[section])

            if section == self.whereami:  # the active tab
                oldclass = sect_info['link_class']
                sect_info['link_class'] = "%s %s" %(oldclass, self.meta['active_class'])

            if section == self.visible[-1]: # the last tab
                oldclass = sect_info['item_class']
                sect_info['item_class'] = "%s %s" %(oldclass, self.meta['end_class'])

            if sect_info['id'].startswith('%s'): # id needs a section sub
                sect_info['id'] = sect_info['id'] %section
                
            sect_info['url'] = self.get_url_node(sect_info['url']).render(context)
            sect_info['text'] = _(sect_info['text'])
            sections.append(sect_info)
            
        return sections

    #@@ cache this? doesn't change much
    def render(self, context):
        sections = self.compile_sections(context)
        info = dict(active=self.whereami,
                    sections=sections,
                    config=self.config)
        return loader.render_to_string(self.template, info)

    @property
    def meta(self):
        return self.config['meta']

    @property
    def visible(self):
        return self.meta['visible'].split()


def export_default_config(path=DEFAULT_PATH):
    conf = os.path.join(settings.PROJECT_ROOT, path)
    conf = ConfigMap.load(conf)
    conf = prep_config(conf)
    conf = dict(conf)
    for name, mapping in sorted(conf.items()):
        conf[name]=dict(mapping)
    return pformat(conf)




