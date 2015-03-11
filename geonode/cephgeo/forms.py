from django import forms
from django.core.exceptions import ValidationError

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit

class DataInputForm(forms.Form):
    data = forms.CharField(widget=forms.Textarea(attrs={'style' : 'resize:none; width:100%; height:60%;', 'wrap' : 'virtual'}))
    pickled = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Data output from bulk_upload.py:',
                'data',
                'pickled',
            ),
            ButtonHolder(
                Submit('submit', 'Submit', css_class='button white')
            )
        )
        super(DataInputForm, self).__init__(*args, **kwargs)
        self.fields['pickled'].initial  = True
