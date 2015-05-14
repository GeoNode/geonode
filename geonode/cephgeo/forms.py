from django import forms
from django.core.exceptions import ValidationError
from geonode.cephgeo.models import DataClassification

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Button
from crispy_forms.bootstrap import FormActions

class DataInputForm(forms.Form):
    data = forms.CharField(widget=forms.Textarea(attrs={'style' : 'resize:none; width:100%; height:60%;', 'wrap' : 'virtual'}))
    pickled = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Metadata output from bulk_upload.py:',
                'data',
                'pickled',
            ),
            ButtonHolder(
                Submit('submit', 'Submit', css_class='button white')
            )
        )
        super(DataInputForm, self).__init__(*args, **kwargs)
        self.fields['pickled'].initial  = True

class RequestDataClassForm(forms.Form):
    LAZ = forms.BooleanField()
    DEM = forms.BooleanField()
    DSM = forms.BooleanField()
    DTM = forms.BooleanField()
    Orthophoto = forms.BooleanField()
    
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Choose which data to download :',
                'LAZ',
                'DEM',
                'DSM',
                'DTM',
                'Orthophoto',
            ),
            FormActions(
                Submit('submit', 'Create FTP Folder', css_class='button white'),
                Button('clear', 'Remove All Items', css_class='button white')
            )
        )
        super(RequestDataClassForm, self).__init__(*args, **kwargs)

class UserRegistrationForm1(forms.Form):
    name_of_requestor = forms.CharField(
        label = "Name of requestor",
        max_length = 80,
        required = True,
    )
    organization = forms.CharField(
        label = "Office/Organization",
        max_length = 80,
        required = True,
    )
    local_or_foreign = forms.TypedChoiceField(
        label = "Are you a local or foreign entity?",
        choices = ((0, "Local"), (1, "Foreign")),
        required = True,
    )
    intended_use = forms.TypedChoiceField(
        label = "Intended use of dataset?",
        choices = ((0, "Non-commercial"), (1, "Commercial")),
        required = True,
    )
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'User Registration Form',
                'name_of_requestor',
                'organization',
                'local_or_foreign',
                'intended_use',
            ),
            FormActions(
                Submit('submit', 'Submit', css_class='button white'),
                Button('clear', 'Clear', css_class='button white')
            )
        )
        super(RequestDataClassForm, self).__init__(*args, **kwargs)
    