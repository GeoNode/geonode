from django import template

register = template.Library()


@register.inclusion_tag('maploom/maploom/_maploom_map.html')
def maploom_html(options=None):
    """
    Maploom html template tag.
    """
    return dict()


@register.inclusion_tag('maploom/maploom/_maploom_js.html')
def maploom_js(options=None):
    """
    Maploom js template tag.
    """
    return dict()
