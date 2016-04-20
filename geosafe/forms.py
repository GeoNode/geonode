# coding=utf-8
from geosafe.tasks.headless.analysis import filter_impact_function

__author__ = 'ismailsunni'

import logging

from django.forms import models
from django import forms

from geonode.layers.models import Layer

from geosafe.models import Analysis

LOG = logging.getLogger(__name__)


class AnalysisCreationForm(models.ModelForm):
    """A form for creating an event."""

    class Meta:
        model = Analysis
        fields = (
            'exposure_layer',
            'hazard_layer',
            'aggregation_layer',
            'impact_function_id',
            'extent_option',
            'keep',
        )

    exposure_layer = forms.ModelChoiceField(
        label='Exposure Layer',
        required=True,
        queryset=Layer.objects.filter(metadata__layer_purpose='exposure'),
        widget=forms.Select(
            attrs={'class': 'form-control'})
    )

    hazard_layer = forms.ModelChoiceField(
        label='Hazard Layer',
        required=True,
        queryset=Layer.objects.filter(metadata__layer_purpose='hazard'),
        widget=forms.Select(
            attrs={'class': 'form-control'})
    )

    aggregation_layer = forms.ModelChoiceField(
        label='Aggregation Layer',
        required=False,
        queryset=Layer.objects.filter(metadata__layer_purpose='aggregation'),
        widget=forms.Select(
            attrs={'class': 'form-control'})
    )

    if_id_list = filter_impact_function.delay().get()

    impact_function_id = forms.ChoiceField(
        label='Impact Function ID',
        required=True,
        choices=[(id, id) for id in if_id_list]
    )

    keep = forms.BooleanField(
        label='Save Analysis',
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        exposure_layer = kwargs.pop('exposure_layer', None)
        hazard_layer = kwargs.pop('hazard_layer', None)
        impact_function_ids = kwargs.pop('impact_functions', None)
        super(AnalysisCreationForm, self).__init__(*args, **kwargs)
        if exposure_layer:
            self.fields['exposure_layer'].queryset = exposure_layer
        if hazard_layer:
            self.fields['hazard_layer'].queryset = hazard_layer
        if impact_function_ids:
            self.fields['impact_function_id'].choices = impact_function_ids

    def save(self, commit=True):
        instance = super(AnalysisCreationForm, self).save(commit=False)
        instance.user = self.user
        instance.save()
        return instance
