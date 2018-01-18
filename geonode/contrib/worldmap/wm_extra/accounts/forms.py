from __future__ import unicode_literals
from django.utils.safestring import mark_safe
import re

try:
    from collections import OrderedDict
except ImportError:
    OrderedDict = None

from django import forms
from django.utils.translation import ugettext_lazy as _

from django.contrib import auth
from django.conf import settings
from django.contrib.auth import get_user_model
from account.conf import settings
from account.hooks import hookset
from account.models import EmailAddress, SignupCode

alnum_re = re.compile(r"^\w+$")

def get_user_lookup_kwargs(kwargs):
    result = {}
    username_field = getattr(get_user_model(), "USERNAME_FIELD", "username")
    for key, value in kwargs.items():
        result[key.format(username=username_field)] = value
    return result

class SignupForm(forms.Form):
    
    username = forms.CharField(
        label=_("Username"),
        max_length=30,
        widget=forms.TextInput(),
        required=False
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(render_value=False)
    )
    password_confirm = forms.CharField(
        label=_("Password (again)"),
        widget=forms.PasswordInput(render_value=False)
    )
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.TextInput(), required=True)

    code = forms.CharField(
        max_length=64,
        required=False,
        widget=forms.HiddenInput()
    )

    if (settings.USE_CUSTOM_ORG_AUTHORIZATION):
	is_org_member = forms.TypedChoiceField(coerce=lambda x: bool(int(x)),
        choices=((1, _(u'Yes')), (0, _(u'No'))),
        widget=forms.RadioSelect,
        initial=0, label=settings.CUSTOM_ORG_AUTH_TEXT
        )
    agree_tos = forms.BooleanField(
	label=mark_safe("I agree to the <a href='/upload_terms'>Terms and Conditions</a>")		
     )
    
    def clean_username(self):
        if not alnum_re.search(self.cleaned_data["username"].replace('.', '')):
            raise forms.ValidationError(_("Usernames can only contain letters, numbers, dots and underscores."))
        User = get_user_model()
        lookup_kwargs = get_user_lookup_kwargs({
            "{username}__iexact": self.cleaned_data["username"]
        })
        qs = User.objects.filter(**lookup_kwargs)
        if not qs.exists():
            return self.cleaned_data["username"]
        raise forms.ValidationError(_("This username is already taken. Please choose another."))

    def clean_email(self):
        value = self.cleaned_data["email"]
        qs = EmailAddress.objects.filter(email__iexact=value)
        if not qs.exists() or not settings.ACCOUNT_EMAIL_UNIQUE:
            return value
        raise forms.ValidationError(_("A user is registered with this email address."))

    def clean(self):
        if "password" in self.cleaned_data and "password_confirm" in self.cleaned_data:
            if self.cleaned_data["password"] != self.cleaned_data["password_confirm"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data


class SignupCodeForm(forms.ModelForm):

    username = forms.CharField(max_length=30, required=False)
    
    class Meta:
        model = SignupCode
        fields = ('email', )
