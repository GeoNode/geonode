from django import forms
from crispy_forms.helper import FormHelper as helper
from crispy_forms.layout import Layout, Fieldset, Div, Field, Submit, ButtonHolder
from crispy_forms.bootstrap import FormActions
from .models import AutomationJob
from django.core.urlresolvers import reverse
from model_utils import Choices
from django.utils.translation import ugettext_lazy as _
from geonode.cephgeo.models import DataClassification
from django_enumfield import enum


class MetaDataJobForm(forms.ModelForm):
    """Form for the model ``AutomationJob``.
    """
    class Meta:
        model = AutomationJob
        fields = ['input_dir', 'output_dir', 'datatype', 'processor', 'target_os']

    # datatype = forms.ModelChoiceField(
    #    queryset=AutomationJob.objects.all()
    # )

    def __init__(self, *args, **kwargs):
        super(MetaDataJobForm, self).__init__(*args, **kwargs)
        self.helper = helper()
        self.helper.form_method = 'post'
        self.helper.field_class = 'col-md-6 col-md-offset-1'
        self.helper.layout = Layout(
            Fieldset('',
                     Div(
                         Field('input_dir', css_class='form-control'),
                         Field('output_dir', css_class='form-control'),

                     ),
                     Div(

                         Field('datatype'),
                         Field('processor'),
                         Field('target_os'),
                     ),
                     ),
            ButtonHolder(
                Submit('submit', 'Submit')
            )
        )
        # self.helper.add_input(Submit('submit', 'Submit'))
