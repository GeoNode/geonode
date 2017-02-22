import os
import traceback

from django import forms
from django.forms import widgets
from django.utils.translation import ugettext_lazy as _

from captcha.fields import ReCaptchaField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, HTML, Div, Column, Row, Field
from crispy_forms.bootstrap import PrependedText, InlineRadios
from model_utils import Choices

from geonode.datarequests.models import DataRequestProfile, DataRequest, ProfileRequest
from geonode.layers.forms import NewLayerUploadForm, LayerUploadForm, JSONField
from geonode.documents.models import Document
from geonode.documents.forms import DocumentCreateForm
from geonode.people.models import OrganizationType, Profile

from .models import DataRequest, ProfileRequest, LipadOrgType

class ProfileRequestEditForm(forms.ModelForm):
    
    ORG_TYPE_CHOICES = LipadOrgType.objects.values_list('val', 'val')
    # Choices that will be used for fields
    LOCATION_CHOICES = Choices(
        ('local', _('Local')),
        ('foreign', _('Foreign')),
    )
    
    REQUEST_LEVEL_CHOICES = Choices(
        ('institution', _('Academic/ Research Institution')),
        ('faculty', _('Faculty')),
        ('student', _('Student')),
    )
    
    class Meta:
        model = ProfileRequest
        
        fields = (
            'first_name',
            'middle_name',
            'last_name',
            'organization',
            # Non-commercial requester field
            'organization_other',
            # Academe requester fields
            'request_level',
            'funding_source',
            'is_consultant',

            'location',
            'email',
            'contact_number',
            'additional_remarks',
        )
        
    org_type = forms.ChoiceField(
        label = _('Organization Type'),
        choices = ORG_TYPE_CHOICES,
        initial = "Other",
        required = True
    )
    
    def __init__(self, *args, **kwargs):
        super(ProfileRequestEditForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset('Editting Profile Request',
                Div(
                    Field('first_name', css_class='form-control'),
                    css_class='form-group'
                ),
                Div(
                    Field('middle_name', css_class='form-control'),
                    css_class='form-group'
                ),
                Div(
                    Field('last_name', css_class='form-control'),
                    css_class='form-group'
                ),
                Div(
                    Field('organization', css_class='form-control'),
                    css_class='form-group'
                ),
                Div(
                    Field('org_type', css_class='form-control'),
                    css_class='form-group'
                ),
                Fieldset('Academe',
                    Div(
                        Field('request_level', css_class='form-control'),
                        css_class='form-group'
                    ),
                    Div(
                        Field('funding_source', css_class='form-control'),
                        css_class='form-group'
                    ),
                    Field('is_consultant'),
                    css_class='academe-fieldset',
                ),

                    Div(
                        Field('organization_other', css_class='form-control'),
                        css_class='form-group'
                    ),

                Div(
                    Field('location', css_class='form-control'),
                    css_class='form-group'
                ),
                Div(
                    Field('email', css_class='form-control'),
                    css_class='form-group'
                ),
                Div(
                    Field('contact_number', css_class='form-control'),
                    css_class='form-group'
                ),
                Div(
                    Field('additional_remarks', css_class='form-control'),
                    css_class='form-group'
                ),
            )
        )
        
    def clean_first_name(self):
        fname = self.cleaned_data.get('first_name').strip()
        if len(fname)<1:
            raise forms.ValidationError("You have entered an empty first name")

        return fname

    def clean_middle_name(self):
        mname = self.cleaned_data.get('middle_name').strip()
        if len(mname)<1 or not mname:
            mname = '_'
        return mname

    def clean_last_name(self):
        lname = self.cleaned_data.get('last_name').strip()
        if len(lname)<1:
            raise forms.ValidationError("You have entered an empty last name")

        return lname

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user_emails = Profile.objects.all().values_list('email', flat=True)
        if email in user_emails:
            raise forms.ValidationError(
                'That email is already being used by a registered user. lease login with your account instead.')

        return email

    def clean_organization(self):
        organization = self.cleaned_data.get('organization')

        if len(organization) > 64:
            raise forms.ValidationError(
                'Organization name can only be 64 characters')

        return organization

    def clean_funding_source(self):
        funding_source = self.cleaned_data.get('funding_source')
        org_type = self.cleaned_data.get('org_type')
        #intended_use_of_dataset = self.cleaned_data.get('intended_use_of_dataset')
        if (#intended_use_of_dataset == 'noncommercial' and
                "Academe" in org_type and
                not funding_source):
            raise forms.ValidationError(
                'This field is required.')
        return funding_source
        
    def clean_organization_other(self):
        organization_other = self.cleaned_data.get('organization_other')
        org_type = self.cleaned_data.get('org_type')
        if (org_type == "Other" and
                not organization_other):
            raise forms.ValidationError(
                'This field is required.')
        return organization_other
