from django.db import models
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils import dateformat
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext as _
from django.utils.encoding import iri_to_uri
from django.utils.http import urlquote
from django_enumfield import enum
from django.core import validators

from model_utils import Choices

from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.people.models import Profile
from .profile_request import ProfileRequest
from .base_request import BaseRequest

class DataRequest(BaseRequest):

    DATA_TYPE_CHOICES = Choices(
        ('interpreted', _('Interpreted')),
        ('raw', _('Raw')),
        ('processed', _('Processed')),
        ('other', _('Other')),
    )
    
    DATASET_USE_CHOICES = Choices(
        ('commercial', _('Commercial')),
        ('noncommercial', _('Non-commercial')),
    )

    REJECTION_REASON_CHOICES = Choices(
        ('reason1', _('Reason 1')),
        ('reason2', _('Reason 2')),
        ('reason3', _('Reason 3')),
    )


    profile_request = models.ForeignKey(
        ProfileRequest,
        null=True,
        blank=True
    )

    jurisdiction_shapefile = models.ForeignKey(Layer, null=True, blank=True)

    project_summary = models.TextField(_('Summary of Project/Program'), null=True, blank=True)
    
    data_type_requested = models.CharField(
        _('Type of Data Requested'),
        choices=DATA_TYPE_CHOICES,
        default=DATA_TYPE_CHOICES.processed,
        max_length=15,
    )    

    purpose = models.TextField(_('Purpose of Data'), null=True, blank = True)
    
    intended_use_of_dataset = models.CharField(
        _('Intended Use of Dataset'),
        choices=DATASET_USE_CHOICES,
        default=DATASET_USE_CHOICES.commercial,
        max_length=15,
    )

    #For place name
    place_name = models.CharField(
        _('Geolocation name provided by Google'),
        null=True,
        blank=True,
        max_length=50,
    )

    area_coverage = models.DecimalField(
        _('Area of Coverage'),
        max_digits=30,
        decimal_places=4,
        help_text=_('Sqr KMs'),
        default=0,
        null=True,
        blank=True,
    )

    #For jurisdiction data size
    juris_data_size = models.FloatField(
        _('Data size of requested jurisdiction in bytes'),
        null=True,
        blank=True,
        default = 0
    )

    #For request letter
    request_letter= models.ForeignKey(Document, null=True, blank=True)

    class Meta:
        app_label = "datarequests"
        verbose_name = _('Data Request Profile')
        verbose_name_plural = _('Data Request Profiles')
        ordering = ('-created',)

    def __init__(self, *args, **kwargs):
        super(DataRequest, self).__init__(*args, **kwargs)
        self.status = BaseRequest.STATUS.unconfirmed
        self.request_type = BaseRequest.REQUEST_TYPE.data

    def __unicode__(self):
        return (_('{} request by {} {} {} of {}')
            .format(
                self.status,
                unidecode(self.get_first_name()),
                unidecode(self.get_last_name()),
                unidecode(self.get_organization()),
            ))

    def get_absolute_url(self):
        return reverse('datarequests:data_request_details', kwargs={'pk': self.pk})

    def assign_jurisdiction(self):
        # Link shapefile to account
        uj = None
        try:
            uj = UserJurisdiction.objects.get(user=self.profile)
        except ObjectDoesNotExist as e:
            pprint("No previous jurisdiction shapefile set")
            uj = UserJurisdiction()
            uj.user = self.profile
        finally:
            uj.jurisdiction_shapefile = self.jurisdiction_shapefile
            uj.save()
        #Add view permission on resource
        resource = self.jurisdiction_shapefile
        perms = resource.get_all_level_info()
        perms["users"][self.profile.username]=["view_resourcebase"]
        resource.set_permissions(perms)

    def get_first_name(self):
        if self.profile:
            return self.profile.first_name
        if self.profile_request:
            return self.profile_request.first_name

    def get_last_name(self):
        if self.profile:
            return self.profile.last_name
        if self.profile_request:
            return self.profile_request.last_name
    
    def get_contact_number(self):
        if self.profile:
            return self.profile.contact_number
        if self.profile_request:
            return self.profile_request.contact_number
            
    def get_organization(self):
        if self.profile:
            return self.profile.organization
        if self.profile_request:
            return self.profile_request.organization
            
    def get_organization_type(self):
        if self.profile_request:
            return self.profile_request.get_organization_type()
        else:
            return None
    
    def to_values_list(self, fields=['id','name','email','contact_number', 'organization', 'project_summary', 'created','status', 'data_size','area_coverage']):
        out = []
        for f in fields:
            if f  is 'id':
                out.append(getattr(self, 'pk'))
            elif f is 'name':
                first_name = unidecode(self.get_first_name())
                last_name = unidecode(self.get_last_name())
                out.append(first_name+" "+last_name)
            elif f is 'created':
                created = getattr(self, f)
                out.append( str(created.month) +"/"+str(created.day)+"/"+str(created.year))
            elif f == 'status update':
                date_of_action = getattr(self, 'status_changed')
                if date_of_action:
                    out.append(str(date_of_action.month)+"/"+str(date_of_action.day)+"/"+str(date_of_action.year))
                else:
                    out.append('')
            elif f is 'organization_type':
                out.append(self.get_organization_type)
            elif f is 'has_letter':
                if self.request_letter:
                    out.append('yes')
                else:
                    out.append('no')
            elif f is 'has_shapefile':
                if self.jurisdiction_shapefile:
                    out.append('yes')
                else:
                    out.append('no')
            elif f is 'rejection_reason':
                out.append(str(getattr(self,'rejection_reason')))
            elif f is 'juris_data_size':
                out.append(str(getattr(self,'juris_data_size')))
            elif f is 'area_coverage':
                out.append(str(getattr(self,'area_coverage')))
            else:
                val = getattr(self, f)
                if isinstance(val, unicode):
                    out.append(unidecode(val))
                else:
                    out.append(str(val))

        return out

    def send_approval_email(self, username):
        site = Site.objects.get_current()
        profile_url = (
            str(site) +
            reverse('profile_detail', kwargs={'username': username})
        )
        profile_url = iri_to_uri(profile_url)

        text_content = email_utils.DATA_APPROVAL_TEXT.format(
             unidecode(self.first_name),
             local_settings.LIPAD_SUPPORT_MAIL
         )

        html_content =email_utils.DATA_APPROVAL_HTML.format(
             unidecode(self.first_name),
             local_settings.LIPAD_SUPPORT_MAIL,
             local_settings.LIPAD_SUPPORT_MAIL
         )

        email_subject = _('[LiPAD] Data Request Status')
        self.send_email(email_subj,text_content,html_content)

    def send_rejection_email(self):

        additional_details = 'Additional Details: ' + str(self.additional_rejection_reason)

        text_content = email_utils.DATA_REJECTION_TEXT.format(
             unidecode(self.first_name),
             self.rejection_reason,
             additional_details,
             local_settings.LIPAD_SUPPORT_MAIL,
         )

        html_content =email_utils.DATA_REJECTION_HTML.format(
             unidecode(self.first_name),
             self.rejection_reason,
             additional_details,
             local_settings.LIPAD_SUPPORT_MAIL,
             local_settings.LIPAD_SUPPORT_MAIL
        )

        email_subject = _('[LiPAD] Data Request Status')
        self.send_email(email_subj,text_content,html_content)
