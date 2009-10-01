"""
Tag for rendering a context sensitive and extendable navigation
"""
from django import template
from django.utils.translation import ungettext
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat

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
    return NavBar()


class NavBar(template.Node):
    """
    Renderer for the nav bar
    """
    def __init__(self, whereami):
        self.whereami = whereami
    def render(self, context):
        import pdb;pdb.set_trace()




