from django import forms
from django.core.exceptions import ValidationError

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Button
from crispy_forms.bootstrap import FormActions

class UserRegistrationForm1(forms.Form):
    name_of_requestor = forms.CharField(
        label = "Name of Requestor",
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
                'Page 1',
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
        super(UserRegistrationForm1, self).__init__(*args, **kwargs)

class UserRegistrationForm2(forms.Form):
    project_summary = forms.CharField(
        label = "Summary of Project/Program",
        required = True,
    )
    organization_type = forms.TypedChoiceField(
        label = "Type of Organization",
        choices = ((2, "Government Agency/Local Government Unit"),
                   (3, "Academe"),
                   (4, "International NGO"),
                   (5, "Local NGO"),
                   (6, "Private"),
                   (7, "Other"),),
        
        required = True,
    )
    other_org_type = forms.CharField(
        label = "If 'Type of Organization' is 'Other' please specify below:",
        max_length = 80,
        required = True,
    )
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Page 2 (Non-commercial)',
                'project_summary',
                'organization_type',
                'other_org_type',
            ),
            FormActions(
                Submit('submit', 'Submit', css_class='button white'),
                Button('clear', 'Clear', css_class='button white')
            )
        )
        super(UserRegistrationForm2, self).__init__(*args, **kwargs)

class UserRegistrationForm3(forms.Form):
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Page 3 (Non-commercial/Academe)',
                'request_level',
                'funding_source',
                'consultant_status',
            ),
            FormActions(
                Submit('submit', 'Submit', css_class='button white'),
                Button('clear', 'Clear', css_class='button white')
            )
        )
        super(UserRegistrationForm2, self).__init__(*args, **kwargs)
    
