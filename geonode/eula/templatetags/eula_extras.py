from django import template
register = template.Library()

@register.inclusion_tag('eula_text.html')
def show_eula(): # Only one argument.
    """Shows the EULA HTML Element"""
    return

@register.inclusion_tag('eula_dialog.html')
def eula_modal_dialog(target_url): # Only one argument.
    """Shows the EULA HTML Element"""
    return {'target_url' : target_url}

@register.inclusion_tag('eula_nested_modal.html')
def eula_nested_modal_dialog(next_modal):
    """Shows the EULA HTML Element"""
    return {'next_modal' : next_modal}

register.filter('show_eula', show_eula)
register.filter('eula_modal_dialog', eula_modal_dialog)
register.filter('eula_nested_modal_dialog', eula_nested_modal_dialog)
