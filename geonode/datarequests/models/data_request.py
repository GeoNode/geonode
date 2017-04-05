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
from model_utils.models import StatusModel
from pprint import pprint
from unidecode import unidecode

from geonode.cephgeo.models import UserJurisdiction
from geonode.datarequests import email_utils
from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.people.models import Profile
from .profile_request import ProfileRequest
from .base_request import BaseRequest
from .suc_directory import SUC_Contact
from taggit.managers import TaggableManager
from taggit.models import GenericTaggedItemBase, TagBase

import geonode.local_settings as local_settings

class SUCRequestTag (TagBase):
    class Meta:
        app_label = "datarequests"


class SUCTaggedRequest (GenericTaggedItemBase):
    tag = models.ForeignKey(SUCRequestTag, related_name='SUC_request_tag')
    
    class Meta:
        app_label = "datarequests"

class DataRequest(BaseRequest, StatusModel):

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
    
    data_type = TaggableManager(_('data_types'), blank=True, help_text="Data Type Selected")
    
    data_class_other = models.CharField(
        _('Requester-specified Data Type'),
        null = True,
        blank = True,
        max_length = 50
    )
    
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
    place_name = models.TextField(
        _('Geolocation name provided by Google'),
        null=True,
        blank=True
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
    
    suc = TaggableManager(_('SUCs'),blank=True, help_text="SUC jurisdictions within this ROI", 
        through=SUCTaggedRequest, related_name="suc_request_tag")
        
    suc_notified = models.BooleanField(null=False,blank=False,default=False)
    suc_notified_date = models.DateTimeField(null=True,blank=True)
    forwarded = models.BooleanField(null=False,blank=False,default=False)
    forwarded_date =  models.DateTimeField(null=True,blank=True)

    class Meta:
        app_label = "datarequests"
        verbose_name = _('Data Request')
        verbose_name_plural = _('Data Requests')
        ordering = ('-created',)

    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        #self.status = self.STATUS.unconfirmed

    def __unicode__(self):
        if self.profile_request or self.profile:
            return (_('{} request by {} {}')
                .format(
                    self.status,
                    unidecode(self.get_first_name()),
                    unidecode(self.get_last_name()),
                ))
        else:
            return (_('Data request # {}').format(
                self.pk
            ))

    def get_absolute_url(self):
        return reverse('datarequests:data_request_detail', kwargs={'pk': self.pk})

    def set_status(self, status, administrator = None):
        self.status = status
        self.administrator = administrator
        self.save()

    def assign_jurisdiction(self):
        # Link shapefile to account
        uj = None
        try:
            uj = UserJurisdiction.objects.get(user=self.profile)
        except ObjectDoesNotExist:
            uj = UserJurisdiction()
            uj.user = self.profile
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

    def get_email(self):
        if self.profile:
            return self.profile.email
        if self.profile_request:
            return self.profile_request.email

    def get_contact_number(self):
        if self.profile:
            return self.profile.voice
        if self.profile_request:
            return self.profile_request.contact_number

    def get_organization(self):
        if self.profile:
            return self.profile.organization
        if self.profile_request:
            return self.profile_request.organization

    def get_organization_type(self):
        if self.profile_request:
            return self.profile_request.org_type
        elif self.profile:
            return self.profile.org_type
        else:
            return None

    def to_values_list(self, fields=['id','name','email','contact_number', 'organization', 'project_summary', 'created','status', 'data_size','area_coverage','has_profile_request']):
        out = []
        for f in fields:
            if f  is 'id':
                out.append(getattr(self, 'pk'))
            elif f is 'name':
                first_name = unidecode(self.get_first_name())
                last_name = unidecode(self.get_last_name())
                out.append(first_name+" "+last_name)
            elif f is 'email':
                out.append(self.get_email())
            elif f is 'contact_number':
                out.append(self.get_contact_number())
            elif f is 'organization':
                if self.get_organization():
                    out.append(unidecode(self.get_organization()))
                else:
                    out.append(None)
            elif f is 'created':
                created = getattr(self, f)
                out.append( str(created.month) +"/"+str(created.day)+"/"+str(created.year))
            elif f == 'status update':
                date_of_action = getattr(self, 'status_changed')
                if date_of_action:
                    out.append(str(date_of_action.month)+"/"+str(date_of_action.day)+"/"+str(date_of_action.year))
                else:
                    out.append('')
            elif f is 'org_type' or f is 'organization_type':
                out.append(self.get_organization_type())
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
            elif f is 'data_request_status':
                if self.data_request:
                    out.append(data_request.status)
                else:
                    out.append("NA")
            elif f is 'rejection_reason':
                out.append(str(getattr(self,'rejection_reason')))
            elif f is 'place_name':
                out.append(str(getattr(self,'place_name')))
            elif f is 'juris_data_size':
                out.append(str(getattr(self,'juris_data_size')))
            elif f is 'area_coverage':
                out.append(str(getattr(self,'area_coverage')))
            elif f is 'has_profile_request':
                if self.profile_request:
                    out.append('yes')
                else:
                    out.append('no')
            elif f is 'has_account':
                if self.profile:
                    out.append('yes')
                else:
                    out.append('no')
            else:
                try:
                    val = getattr(self, f)
                    if isinstance(val, unicode):
                        out.append(unidecode(val))
                    else:
                        out.append(str(val))
                except Exception:
                    out.append("NA")

        return out

    def send_email(self, subj, msg, html_msg):
        text_content = msg

        html_content = html_msg

        email_subject = _(subj)

        msg = EmailMultiAlternatives(
            email_subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [self.get_email(), ]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    def send_new_request_notif_to_admins(self, request_type="Data"):
        site = Site.objects.get_current()
        text_content = email_utils.NEW_REQUEST_EMAIL_TEXT.format(
            request_type,
            settings.BASEURL + self.get_absolute_url()
        )

        html_content=email_utils.NEW_REQUEST_EMAIL_HTML.format(
            request_type,
            settings.BASEURL + self.get_absolute_url(),
            settings.BASEURL + self.get_absolute_url()
        )

        email_subject = "[LiPAD] A new request has been submitted"
        self.send_email(email_subject,text_content,html_content)

    def send_approval_email(self, username):
        site = Site.objects.get_current()
        profile_url = (
            reverse('profile_detail', kwargs={'username': username})
        )
        profile_url = iri_to_uri(profile_url)

        text_content = email_utils.DATA_APPROVAL_TEXT.format(
             unidecode(self.get_first_name()),
             local_settings.LIPAD_SUPPORT_MAIL
         )

        html_content =email_utils.DATA_APPROVAL_HTML.format(
             unidecode(self.get_first_name()),
             local_settings.LIPAD_SUPPORT_MAIL,
             local_settings.LIPAD_SUPPORT_MAIL
         )

        email_subject = _('[LiPAD] Data Request Status')
        self.send_email(email_subject,text_content,html_content)

    def send_rejection_email(self):

        additional_details = 'Additional Details: ' + str(self.additional_rejection_reason)

        text_content = email_utils.DATA_REJECTION_TEXT.format(
             unidecode(self.get_first_name()),
             self.rejection_reason,
             additional_details,
             local_settings.LIPAD_SUPPORT_MAIL,
         )

        html_content =email_utils.DATA_REJECTION_HTML.format(
             unidecode(self.get_first_name()),
             self.rejection_reason,
             additional_details,
             local_settings.LIPAD_SUPPORT_MAIL,
             local_settings.LIPAD_SUPPORT_MAIL
        )

        email_subject = _('[LiPAD] Data Request Status')
        self.send_email(email_subject,text_content,html_content)
        
    def send_suc_notification(self, suc=None):
        if not suc:
            if len(self.suc.names()) > 1:
                suc = "UPD"
            else:
                suc = self.suc.names()[0]
            
        suc_contacts = SUC_Contact.objects.filter(institution_abrv=suc).exclude(position="Program Leader")
        suc_pl = SUC_Contact.objects.get(institution_abrv=suc, position="Program Leader")
        organization = ""
        if self.get_organization():
            organization = unidecode(self.get_organization())
        
        data_classes = ""
        for n in self.data_type.names():
            data_classes += str(n)
        
        data_classes += str(self.data_class_other)
            
        
        text_content = email_utils.DATA_SUC_REQUEST_NOTIFICATION_TEXT.format(
            suc_pl.salutation,
            suc_pl.name,
            unidecode(self.get_first_name()),
            unidecode(self.get_last_name()),
            organization,
            self.get_email(),
            self.project_summary,
            data_classes,
            self.purpose,
        )
        
        html_content = email_utils.DATA_SUC_REQUEST_NOTIFICATION_HTML.format(
            suc_pl.salutation,
            suc_pl.name,
            unidecode(self.get_first_name()),
            unidecode(self.get_last_name()),
            organization,
            self.get_email(),
            self.project_summary,
            data_classes,
            self.purpose,
        )
        
        cc = suc_contacts.values_list('email_address',flat = True)
        
        email_subject = _('[LiPAD] Data Request Forwarding')
        
        msg = EmailMultiAlternatives(
            email_subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [suc_pl.email_address, ],
            cc = cc
        )
        
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        self.suc_notified =True
        self.suc_notified_date = timezone.now()
        self.save()
            
    
    def send_jurisdiction(self, suc=None):
        if not suc:
            if len(self.suc.names()) == 1:
                suc = self.suc.names()[0]
            else:
                suc = "UPD"
                
        suc_contacts = SUC_Contact.objects.filter(institution_abrv=suc).exclude(position="Program Leader")
        suc_pl = SUC_Contact.objects.get(institution_abrv=suc, position="Program Leader")
        
        text_content = email_utils.DATA_SUC_JURISDICTION_TEXT.format(
            suc_pl.salutation,
            suc_pl.name,
            settings.BASEURL+self.jurisdiction_shapefile.get_absolute_url(),
        )
        
        html_content = email_utils.DATA_SUC_JURISDICTION_HTML.format(
            suc_pl.salutation,
            suc_pl.name,
            settings.BASEURL+self.jurisdiction_shapefile.get_absolute_url(),
            settings.BASEURL+self.jurisdiction_shapefile.get_absolute_url(),
        )
        
        cc = suc_contacts.values_list('email_address',flat = True)
        
        email_subject = _('[LiPAD] Data Request Forwarding')
        
        msg = EmailMultiAlternatives(
            email_subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [suc_pl.email_address, ],
            cc = cc
        )
        
        if not suc == "UPD":
            resource = self.jurisdiction_shapefile
            perms = resource.get_all_level_info()
            perms["users"][str(suc).lower()]=["view_resourcebase","download_resourcebase"]
            resource.set_permissions(perms)
            
        
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        self.forwarded = True
        self.forwarded_date = timezone.now()
        self.save()
        
    def notify_user_preforward(self, suc=None):
        if not suc:
            if len(self.suc.names()) == 1:
                suc = self.suc.names()[0]
            else:
                suc = "UPD"
                
        suc_contact = SUC_Contact.objects.get(institution_abrv=suc, position="Program Leader")
        
        text_content = email_utils.DATA_USER_PRE_FORWARD_NOTIFICATION_TEXT.format(
            self.get_first_name(),
            self.get_last_name(),
            suc_contact.institution_full,
            suc_contact.institution_abrv,
            suc_contact.salutation,
            suc_contact.name
        )
        
        
        html_content = email_utils.DATA_USER_PRE_FORWARD_NOTIFICATION_HTML.format(
            self.get_first_name(),
            self.get_last_name(),
            suc_contact.institution_full,
            suc_contact.institution_abrv,
            suc_contact.salutation,
            suc_contact.name
        )
        
        email_subject = _('[LiPAD] Data Request Forwarding')
        
        msg = EmailMultiAlternatives(
            email_subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [self.get_email(), ],
        )
        
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    
    def notify_user_forward(self, suc=None):
        if not suc:
            if len(self.suc.names()) == 1:
                suc = self.suc.names()[0]
            else:
                suc = "UPD"
        
        text_content = email_utils.DATA_USER_FORWARD_NOTIFICATION_TEXT.format(
            self.get_first_name(),
            self.get_last_name(),
            suc
        )
        
        
        html_content = email_utils.DATA_USER_FORWARD_NOTIFICATION_HTML.format(
            self.get_first_name(),
            self.get_last_name(),
            suc
        )
        
        email_subject = _('[LiPAD] Data Request Forwarding')
        
        msg = EmailMultiAlternatives(
            email_subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [self.get_email(), ],
        )
        
        msg.attach_alternative(html_content, "text/html")
        msg.send()

###utility functions

        
        
