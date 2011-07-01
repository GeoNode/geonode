# -*- coding: UTF-8 -*-
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from registration.forms import RegistrationFormUniqueEmail
from django.utils.translation import ugettext_lazy as _
from geonode.maps.models import Contact
from registration.models import RegistrationProfile

attrs_dict = { 'class': 'required' }

class UserRegistrationForm(RegistrationFormUniqueEmail):
    if (settings.USE_CUSTOM_ORG_AUTHORIZATION):
        is_org_member = forms.TypedChoiceField(coerce=lambda x: bool(int(x)),
                   choices=((1, _(u'Yes')), (0, _(u'No'))),
                   widget=forms.RadioSelect,
                   initial=0, label=settings.CUSTOM_ORG_AUTH_TEXT
                )

    username = forms.RegexField(regex=r'^\w+$',
                                max_length=30,
                                widget=forms.TextInput(attrs=attrs_dict),
                                label=_(u'username'),
                                error_messages = {
                                                          'invalid': _(u'Username must contain only letters, numbers, and underscores, and start with a letter'),
                                                          }
                                )
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=75)),
                             label=_(u'email address'))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_(u'password'))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_(u'password (again)'))

    def save(self, profile_callback=None):
        new_user = RegistrationProfile.objects.create_inactive_user(username=self.cleaned_data['username'],
        password=self.cleaned_data['password1'],
        email=self.cleaned_data['email'],
        site = Site.objects.get_current())
        new_profile = Contact(user=new_user)
        new_profile.email = new_user.email
        if (settings.USE_CUSTOM_ORG_AUTHORIZATION):
            new_profile.is_org_member=self.cleaned_data['is_org_member']
        new_profile.save()
        
        return new_user