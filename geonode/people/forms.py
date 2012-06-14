# -*- coding: utf-8 -*-
from geonode.people.models import Contact
from geonode.layers.models import ContactRole
from django import forms
from django.utils.translation import ugettext_lazy as _
from registration.forms import attrs_dict
import taggit


class ForgotUsernameForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
        maxlength=75)),
        label=_(u'Email Address'))


class RoleForm(forms.ModelForm):
    class Meta:
        model = ContactRole
        exclude = ('contact', 'layer')


class PocForm(forms.Form):
    contact = forms.ModelChoiceField(label = "New point of contact",
                                     queryset = Contact.objects.exclude(user=None))


class ContactForm(forms.ModelForm):
    keywords = taggit.forms.TagField()
    class Meta:
        model = Contact
        exclude = ('user',)
