from django import template
from django.template import Context
from django.template.loader import get_template


register = template.Library()


@register.filter
def as_bootstrap(form):
    template = get_template("bootstrap/form.html")
    c = Context({"form": form})
    return template.render(c)


@register.filter
def is_checkbox(field):
    return field.field.widget.__class__.__name__.lower() == "checkboxinput"


@register.filter
def css_class(field):
    return field.field.widget.__class__.__name__.lower()
