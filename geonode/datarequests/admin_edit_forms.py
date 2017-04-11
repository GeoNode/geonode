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

from pprint import pprint

from geonode.cephgeo.models import TileDataClass
from geonode.datarequests.models import DataRequestProfile, DataRequest, ProfileRequest
from geonode.layers.forms import NewLayerUploadForm, LayerUploadForm, JSONField
from geonode.documents.models import Document
from geonode.documents.forms import DocumentCreateForm
from geonode.people.models import OrganizationType, Profile

from .models import DataRequest, ProfileRequest, LipadOrgType
from .forms import ProfileRequestForm, DataRequestForm

class ProfileRequestEditForm(ProfileRequestForm):
    
    ORG_TYPE_CHOICES = LipadOrgType.objects.values_list('val', 'display_val')
    ORDERED_FIELDS =['org_type', 'organization_other','request_level','funding_source']
    LOCATION_CHOICES = Choices(
        ('local', _('Local')),
        ('foreign', _('Foreign')),
    )
    
    REQUEST_LEVEL_CHOICES = Choices(
        ('institution', _('Academic/ Research Institution')),
        ('faculty', _('Faculty')),
        ('student', _('Student')),
    )
    
    org_type = forms.ModelChoiceField(
        label = _('Organization Type'),
        queryset=LipadOrgType.objects.all(),
        required=True,
        to_field_name='val',
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
    
    def __init__(self, *args, **kwargs):
        super(ProfileRequestEditForm, self).__init__(*args, **kwargs)
        self.fields.pop('captcha')
        self.fields.keyOrder = self.ORDERED_FIELDS + [k for k in self.fields.keys() if k not in self.ORDERED_FIELDS]
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
        

class DataRequestEditForm(forms.ModelForm):
    
    ORDERED_FIELDS = ["purpose", "purpose_other", "data_class_requested","data_class_other"]
    
    INTENDED_USE_CHOICES = Choices(
        ('Disaster Risk Management', _('Disaster Risk Management')),
        ('Urban/Land Subdivision Planning',
            _('Urban/Land Subdivision Planning')),
        ('Road/Infrastracture Planning', _('Road/Infrastracture Planning')),
        ('Transport/Traffic Management', _('Transport/Traffic Management')),
        ('Oil/Gas/Geothermal/Quarries/Minerals Exploration',
            _('Oil/Gas/Geothermal/Quarries/Minerals Exploration')),
        ('Biological/Agricultural/Forestry/Marine/Natural Resource Planning',
            _('Biological/Agricultural/Forestry/Marine/Natural Resource Planning')),
        ('Cellular Network Mapping', _('Cellular Network Mapping')),
        ('other', _('Other, please specify:')),
    )
    
    purpose = forms.ChoiceField(
        label =_(u'Purpose of the Data'),
        choices = INTENDED_USE_CHOICES
    )

    purpose_other = forms.CharField(
        label=_(u'Your custom purpose for the data'),
        required=False
    )
    
    data_class_requested = forms.ModelMultipleChoiceField(
        label = _('Types of Data Requested. (Press CTRL to select multiple types)'),
        queryset = TileDataClass.objects.all(),
        to_field_name = 'short_name',
        required = True
    )
    
    class Meta:
        model = DataRequest
        fields = [
            "project_summary",
            "purpose",
            #"data_class_requested",
            "data_class_other",
            "intended_use_of_dataset",
            "additional_remarks"
        ]
        
    def __init__(self, *args, **kwargs):
        super(DataRequestEditForm, self).__init__(*args, **kwargs)
        #self.fields.pop('letter_file')
        self.fields.keyOrder = self.ORDERED_FIELDS + [k for k in self.fields.keys() if k not in self.ORDERED_FIELDS]
        if 'initial' in kwargs: 
            if 'data_type' in kwargs['initial']:
                initial_tags = []
                for t_item in kwargs['initial']['data_type']:
                    initial_tags.append(t_item.tag.name)
                self.fields['data_class_requested'].initial = initial_tags
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Field('project_summary', css_class='form-control'),
                css_class='form-group'
            ),
            Div(
                Field('purpose', css_class='form-control'),
                Div(
                    Field('purpose_other', css_class='form-control'),
                    css_class='col-sm-11 col-sm-offset-1'
                ),
                css_class='form-group'
            ),
            Div(
               Field('data_class_requested', css_class='form-control'),
               css_class='form-group'
            ),
            Div(
                Field('data_class_other', css_class='form-control'),
                css_class='form-group'
            ),
            Div(
                Field('intended_use_of_dataset', css_class='form-control'),
                css_class='form-group'
            ),
            Div(
                Field('additional_remarks', css_class='form-control'),
                css_class='form-group'
            ),
        )
    
    def clean_purpose_other(self):
        purpose = self.cleaned_data.get('purpose')
        purpose_other = self.cleaned_data.get('purpose_other')
        if purpose == self.INTENDED_USE_CHOICES.other:
            if not purpose_other:
                raise forms.ValidationError(
                    'Please state your purpose for the requested data.')
        return purpose_other

    def clean_purpose(self):
        purpose = self.cleaned_data.get('purpose')
        if purpose == self.INTENDED_USE_CHOICES.other:
            purpose_other = self.cleaned_data.get('purpose_other')
            if not purpose_other:
                return purpose
            else:
                return purpose_other
        return purpose
    
    def clean_data_class_other(self):
        data_class_other = self.cleaned_data.get('data_class_other')
        pprint(self.cleaned_data.get('data_class_requested'))
        data_classes = self.clean_data_class_requested()
        #data_classes = [c.short_name for c in self.cleaned_data.get('data_class_requested')]#self.cleaned_data.get('data_class_requested')
        
        if data_classes:
            if 'Other' in data_classes and not data_class_other:
                raise forms.ValidationError(_('This field is required if you selected Other'))
            if 'Other' not in data_classes and data_class_other:
                return None
        return data_class_other

    def clean_data_class_requested(self):
        pprint('admin edit form')
        data_classes = self.cleaned_data.get('data_class_requested')
        pprint("data_classes:"+str(data_classes))
        data_class_list = []
        if data_classes:
            for dc in data_classes:
                data_class_list.append(dc)
            return data_class_list
        else:
            raise forms.ValidationError(
                "Please choose the data class you want to download. If it is not in the list, select 'Other' and indicate the data class in the text box that appears")
