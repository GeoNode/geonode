# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
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
