from django.forms.forms import BoundField
from django.forms.widgets import CheckboxInput, RadioSelect
from django.template import Context
from django.template.loader import get_template
from django import template


register = template.Library()


@register.filter
def as_bootstrap(form):
    template = get_template("bootstrap/form.html")
    c = Context({"form": form})
    return template.render(c)


@register.filter
def is_checkbox(value):
    if not isinstance(value, BoundField):
        return False
    return isinstance(value.field.widget, CheckboxInput)

@register.filter
def is_radio(value):
    if not isinstance(value, BoundField):
        return False
    return isinstance(value.field.widget, RadioSelect)
