from django import template
register = template.Library()

@register.inclusion_tag('eula_text_dream.html')
def show_eula_dream(): # Only one argument.
    """Shows the EULA HTML Element"""
    return
@register.inclusion_tag('eula_text_phillidar1.html')
def show_eula_phillidar1(): # Only one argument.
    """Shows the EULA HTML Element"""
    return
@register.inclusion_tag('eula_text_phillidar2.html')
def show_eula_phillidar2(): # Only one argument.
    """Shows the EULA HTML Element"""
    return

@register.inclusion_tag('eula_dialog.html')
def eula_modal_dialog(target_url): # Only one argument.
    """Shows the EULA HTML Element"""
    return {'target_url' : target_url}

@register.inclusion_tag('eula_nested_dialog.html')
def eula_nested_modal_dialog(next_modal):
    """Shows the EULA HTML Element"""
    return {'next_modal' : next_modal}

register.filter('show_eula_dream', show_eula_dream)
register.filter('show_eula_phillidar1', show_eula_phillidar1)
register.filter('show_eula_phillidar2', show_eula_phillidar2)
register.filter('eula_modal_dialog', eula_modal_dialog)
register.filter('eula_nested_modal_dialog', eula_nested_modal_dialog)
