from geosafe.tasks.analysis import if_list

__author__ = 'ismailsunni'
from datetime import datetime
import logging

from django.forms import models
from django import forms

from geonode.layers.models import Layer

from geosafe.models import Metadata, Analysis

LOG = logging.getLogger(__name__)


class AnalysisCreationForm(models.ModelForm):
    """A form for creating an event."""

    class Meta:
        model = Analysis

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
        required=True,
        queryset=Layer.objects.filter(metadata__layer_purpose='aggregation'),
        widget=forms.Select(
            attrs={'class': 'form-control'})
    )

    if_id_list = if_list()

    impact_function_id = forms.ChoiceField(
        label='Impact Function ID',
        required=True,
        choices=[(id, id) for id in if_id_list]
    )
