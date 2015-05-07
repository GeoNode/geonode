from django import template
register = template.Library()

@register.inclusion_tag('eula_text.html')
def show_eula(): # Only one argument.
    """Shows the EULA HTML Element"""
    return

register.filter('show_eula', show_eula)
