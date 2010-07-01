# -*- coding: UTF-8 -*-
from django import forms
from django.forms.util import flatatt
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

def require(*args):
    pass

class LabelledInput(forms.Widget):
    def __init__(self, name, attrs=None):
        # The 'rows' and 'cols' attributes are required for HTML correctness.
        self.name = name
        super(LabelledInput, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        if value is None: value = ''
        final_attrs = self.build_attrs(attrs)
        return mark_safe( u'<label for="{id}">{name}</label> <input name="{name}"{atts}>{value}</input>'.format(
            id = final_attrs.get(id, ""),
            name = self.name,
            atts = flatatt(final_attrs),
            value = conditional_escape(force_unicode(value))
        ))