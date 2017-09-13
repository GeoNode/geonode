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

from django import forms
import taggit
from geonode.services.models import Service, ServiceLayer
from geonode.services.enumerations import SERVICE_TYPES
from django.utils.translation import ugettext_lazy as _
from geonode.base.models import TopicCategory
from django.conf import settings

def get_classifications():
        return [(x, str(x)) for x in getattr(settings, 'CLASSIFICATION_LEVELS', [])]


def get_caveats():
        return [(x, str(x)) for x in getattr(settings, 'CAVEATS', [])]


def get_provenances():
        default = [('Commodity', 'Commodity'), ('Crowd-sourced data', 'Crowd-sourced data'),
                   ('Derived by trusted agents ', 'Derived by trusted agents '),
                   ('Open Source', 'Open Source'), ('Structured Observations (SOM)',
                                                    'Structured Observations (SOM)'), ('Unknown', 'Unknown')]

        provenance_choices = [(x, str(x)) for x in getattr(settings, 'REGISTRY_PROVENANCE_CHOICES', [])]

        return provenance_choices + default

class CreateServiceForm(forms.Form):
    # name = forms.CharField(label=_("Service Name"), max_length=512,
    #     widget=forms.TextInput(
    #         attrs={'size':'50', 'class':'inputText'}))
    url = forms.CharField(label=_("Service URL"), max_length=512,
                          widget=forms.TextInput(
        attrs={'size': '65', 'class': 'inputText'}))
    name = forms.CharField(label=_('Service name'), max_length=128,
                           widget=forms.TextInput(
        attrs={'size': '65', 'class': 'inputText'}), required=False)
    type = forms.ChoiceField(
        label=_("Service Type"), choices=SERVICE_TYPES, initial='AUTO', required=True)
    # method = forms.ChoiceField(label=_("Service Type"),choices=SERVICE_METHODS,initial='I',required=True)


class ServiceForm(forms.ModelForm):
    classification = forms.ChoiceField(
        label=_("Classification"), choices=get_classifications(), 
        widget=forms.Select(attrs={'cols': 60, 'class': 'inputText'}))
    caveat = forms.ChoiceField(
        label=_("Caveat"), choices=get_caveats(), 
        widget=forms.Select(attrs={'cols': 60, 'class': 'inputText'}))
    provenance = forms.ChoiceField(
        label=_("Provenance"), choices=get_provenances(), 
        widget=forms.Select(attrs={'cols': 60, 'class': 'inputText'}))
    title = forms.CharField(label=_('Title'), max_length=255, widget=forms.TextInput(
        attrs={'size': '60', 'class': 'inputText'}))
    category = forms.ModelChoiceField(
        label=_('Category'),
        queryset=TopicCategory.objects.filter(
            is_choice=True) .extra(
            order_by=['description']))    
    abstract = forms.CharField(
        label=_("Abstract"), widget=forms.Textarea(attrs={'cols': 60}))
    keywords = taggit.forms.TagField(required=False)
    fees = forms.CharField(label=_('Fees'), max_length=1000, widget=forms.TextInput(
        attrs={'size': '60', 'class': 'inputText'}))


    class Meta:
        model = Service
        fields = ('classification', 'caveat', 'title', 'category',
        'description', 'abstract', 'keywords', 'provenance', 'fees', )


class ServiceLayerFormSet(forms.ModelForm):

    class Meta:
        model = ServiceLayer
        fields = ('typename',)
