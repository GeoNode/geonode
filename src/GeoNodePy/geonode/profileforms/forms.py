# -*- coding: UTF-8 -*-
from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from registration.forms import RegistrationFormUniqueEmail
from django.utils.translation import ugettext_lazy as _
from geonode.maps.models import Contact
from registration.models import RegistrationProfile

attrs_dict = { 'class': 'required' }

class ContactProfileForm(ModelForm):
    class Meta:
        model = Contact
        exclude = ('is_harvard',)