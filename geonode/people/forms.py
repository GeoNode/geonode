# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import taggit

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import ugettext_lazy as _

from geonode.base.enumerations import COUNTRIES
from geonode.base.enumerations import PROFESSIONAL_ROLES
from geonode.base.enumerations import USE_ANALYSIS
from geonode.base.models import ContactRole

from allauth.account.forms import SignupForm
from allauth.account.forms import PasswordField

from allauth.account.adapter import get_adapter
from allauth.account.utils import (
    setup_user_email
)

from captcha.fields import ReCaptchaField

# Ported in from django-registration
attrs_dict = {'class': 'required'}


class AllauthReCaptchaSignupForm(forms.Form):

    captcha = ReCaptchaField()

    def signup(self, request, user):
        """ Required, or else it thorws deprecation warnings """
        pass


class ProfileCreationForm(UserCreationForm):

    class Meta:
        model = get_user_model()
        fields = ("username",)

    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        try:
            get_user_model().objects.get(username=username)
        except get_user_model().DoesNotExist:
            return username
        raise forms.ValidationError(
            self.error_messages['duplicate_username'],
            code='duplicate_username',
        )


class ProfileChangeForm(UserChangeForm):

    class Meta:
        model = get_user_model()
        fields = '__all__'


class ForgotUsernameForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=75)),
                             label=_('Email Address'))


class RoleForm(forms.ModelForm):

    class Meta:
        model = ContactRole
        exclude = ('contact', 'layer')


class PocForm(forms.Form):
    contact = forms.ModelChoiceField(label="New point of contact",
                                     queryset=get_user_model().objects.all())


class ProfileForm(forms.ModelForm):
    keywords = taggit.forms.TagField(
        label=_("Keywords"),
        required=False,
        help_text=_("A space or comma-separated list of keywords"))

    class Meta:
        model = get_user_model()
        exclude = (
            'user',
            'password',
            'last_login',
            'groups',
            'user_permissions',
            'username',
            'is_staff',
            'is_superuser',
            'is_active',
            'date_joined'
        )
    
    field_order = [
        "email",
        "username",    
        "first_name",
        "last_name",
        "organization",
        "professional_role",
        "other_role",
        "use_analysis",
        'other_analysis',
        "country",
        "city",
        "password",
        "agree_conditions",
    ]

class CustomUserCreationForm2(SignupForm):

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm2, self).__init__(*args, **kwargs)

    first_name = forms.CharField(label=_("FirstName"),
                               widget=forms.TextInput(
                                   attrs={'placeholder':
                                          _('Firstname')}))
    
    last_name = forms.CharField(label=_("LastName"),
                               widget=forms.TextInput(
                                   attrs={'placeholder':
                                          _('Lastname')}))

    professional_role = forms.ChoiceField(label=_("ProfessionalRole"), choices=PROFESSIONAL_ROLES)

    other_role = forms.CharField(label=_("Other Role"),
                               widget=forms.TextInput(
                                   attrs={'placeholder':
                                          _('Other Role')}))
    
    use_analysis = forms.ChoiceField(label=_("Use Analysis"), choices=USE_ANALYSIS)

    other_analysis = forms.CharField(label=_("Other Analysis"),
                               widget=forms.TextInput(
                                   attrs={'placeholder':
                                          _('Other Analysis')}))

    organization = forms.CharField(label=_("Organization"),
                               widget=forms.TextInput(
                                   attrs={'placeholder':
                                          _('Organization')}))            
    
    country = forms.ChoiceField(label=_('Country'), choices=COUNTRIES)

    city = forms.CharField(label=_("City"),
                               widget=forms.TextInput(
                                   attrs={'placeholder':_('City'),
                                   'autocomplete':'off'}))

    agree_conditions = forms.BooleanField(label=_('AgreeConditions'))

    field_order = [
        "email",
        "email2",  # ignored when not present
        "username",    
        "first_name",
        "last_name",
        "organization",
        "professional_role",
        "other_role",
        "use_analysis",
        "other_analysis",
        "country",
        "city",
        "password1",
        "password2",  # ignored when not present
        "agree_conditions",
    ]

    # city = forms.ChoiceField(label=_('City'), choices=CITIES)
    
    def save(self, request):
        adapter = get_adapter(request)
        user = adapter.new_user(request)
        adapter.save_user(request, user, self)
        self.custom_signup(request, user)
        # TODO: Move into adapter `save_user` ?
        setup_user_email(request, user, [])
        return user

