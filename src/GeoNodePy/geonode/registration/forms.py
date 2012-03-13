from django import forms
from django.utils.translation import ugettext_lazy as _
from registration.forms import attrs_dict


class ForgotUsernameForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
        maxlength=75)),
        label=_(u'Email Address'))
