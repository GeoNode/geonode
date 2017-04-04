from django import forms
from django.core.exceptions import ValidationError

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Button
from crispy_forms.bootstrap import FormActions

class DataInputForm(forms.Form):
    data = forms.CharField(widget=forms.Textarea(attrs={'style' : 'resize:none; width:100%; height:60%;', 'wrap' : 'virtual'}))
    update_grid = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Metadata output from bulk_upload.py:',
                'data',
                'update_grid',
            ),
            ButtonHolder(
                Submit('submit', 'Submit', css_class='button white')
            )
        )
        super(DataInputForm, self).__init__(*args, **kwargs)
        self.fields['update_grid'].initial  = True

class DataDeleteForm(forms.Form):
    data = forms.CharField(widget=forms.Textarea(attrs={'style' : 'resize:none; width:100%; height:60%;', 'wrap' : 'virtual'}))
    update_grid = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Metadata/object list for deletion',
                'data',
                'update_grid',
                'delete_from_ceph',
            ),
            ButtonHolder(
                Submit('submit', 'Submit', css_class='button white')
            )
        )
        super(DataInputForm, self).__init__(*args, **kwargs)
        self.fields['update_grid'].initial  = True
        self.fields['delete_from_ceph'].initial  = False


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
