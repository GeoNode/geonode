from django import forms

from .models import Endpoint


class EndpointForm(forms.ModelForm):
    """
    A form to add a remote endpoint.
    """
    class Meta:
        model = Endpoint
        fields = ['url', 'description', ]
