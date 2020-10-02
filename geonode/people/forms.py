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
from django.utils.translation import ugettext as _

from geonode.base.enumerations import COUNTRIES
from geonode.base.models import ContactRole

from allauth.account.forms import SignupForm

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

class CustomUserCreationForm(SignupForm):
    username = forms.CharField(label=_("Username"),
                               widget=forms.TextInput(
                                   attrs={'placeholder':
                                          _('Username'),
                                          'autofocus': 'autofocus'}))
    
    first_name = forms.CharField(label=_("FirstName"),
                               widget=forms.TextInput(
                                   attrs={'placeholder':
                                          _('Firstname')}))
    
    last_name = forms.CharField(label=_("LastName"),
                               widget=forms.TextInput(
                                   attrs={'placeholder':
                                          _('Lastname')}))
    
    organization = forms.CharField(label=_("Organization"),
                               widget=forms.TextInput(
                                   attrs={'placeholder':
                                          _('Organization')}))
    
    city = forms.CharField(label=_("City"),
                               widget=forms.TextInput(
                                   attrs={'placeholder':
                                          _('City')}))
    
    country = forms.CharField(label=_("Country"),                               
                               widget=forms.TextInput(
                                   attrs={'placeholder':
                                          _('Country')}))

    agree_conditions = forms.BooleanField(label=_("AgreeConditions"))

    

    email = forms.EmailField(widget=forms.TextInput(
        attrs={'type': 'email',
               'placeholder': _('E-mail address')}))
    password1 = forms.CharField(label='Enter password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data['username'].lower()
#        r = User.objects.filter(username=username)
#        if r.count():
#            raise  ValidationError("Username already exists")
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
#        r = User.objects.filter(email=email)
#        if r.count():
#            raise  ValidationError("Email already exists")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("Password don't match")

        return password2

    def save(self, request):
        user = super(CustomUserCreationForm, self).save(request)
        return user
    
class MyCustomSignupForm(SignupForm):

    def save(self, request):

        # Ensure you call the parent class's save.
        # .save() returns a User object.
        user = super(MyCustomSignupForm, self).save(request)

        # Add your own processing here.

        # You must return the original result.
        return user