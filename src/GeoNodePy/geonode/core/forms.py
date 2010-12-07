# -*- coding: UTF-8 -*-
from django import forms
from django.contrib.auth.models import User
from registration.forms import RegistrationFormUniqueEmail
from django.utils.translation import ugettext_lazy as _
from geonode.maps.models import Contact
from registration.models import RegistrationProfile

attrs_dict = { 'class': 'required' }

class UserRegistrationForm(RegistrationFormUniqueEmail):
    is_harvard = forms.ChoiceField(widget=forms.RadioSelect(), choices=((True, 'Yes'),(False, 'No')), initial=False, label="Are you affiliated with Harvard University?")


    def save(self, profile_callback=None):
        new_user = RegistrationProfile.objects.create_inactive_user(username=self.cleaned_data['username'],
        password=self.cleaned_data['password1'],
        email=self.cleaned_data['email'])
        new_profile = Contact(user=new_user, is_harvard=self.cleaned_data['is_harvard'])
        new_profile.save()
        return new_user