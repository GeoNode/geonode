from django.db import models
from django.conf import settings
from django.contrib import messages
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
from django_auth_ldap.backend import LDAPBackend, ldap_error

from model_utils import Choices
from model_utils.models import TimeStampedModel, StatusModel
from pprint import pprint
from unidecode import unidecode
import traceback

from geonode.datarequests import email_utils
from geonode.datarequests.utils import add_to_ad_group, create_login_credentials, create_ad_account
from geonode.documents.models import Document
from geonode.people.models import OrganizationType, Profile
from geonode.groups.models import GroupProfile, GroupMember
from geonode.layers.models import Layer

from geonode.tasks.mk_folder import create_folder
from .base_request import BaseRequest, LipadOrgType


class ProfileRequest(BaseRequest, StatusModel):

    # Choices that will be used for fields
    LOCATION_CHOICES = Choices(
        ('local', _('Local')),
        ('foreign', _('Foreign')),
    )

    STATUS = Choices(
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('cancelled', _('Cancelled')),
        ('rejected', _('Rejected')),
        ('unconfirmed',_('Unconfirmed Email')),
    )

    REQUESTER_TYPE_CHOICES = Choices(
        ('commercial', _('Commercial Requester')),
        ('noncommercial', _('Non-Commercial Requester')),
    )

    REQUEST_LEVEL_CHOICES = Choices(
        ('institution', _('Institution')),
        ('faculty', _('Faculty')),
        ('student', _('Student')),
    )

    REJECTION_REASON_CHOICES = Choices(
        ('reason1', _('Reason 1')),
        ('reason2', _('Reason 2')),
        ('reason3', _('Reason 3')),
    )

    data_request = models.ForeignKey(
        'DataRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="new",
    )

    username = models.CharField(
        _('User name'),
        max_length=50,
        null=True,
        blank=True,
    )

    first_name = models.CharField(_('First Name'), max_length=21)
    middle_name = models.CharField(_('Middle Name'), max_length=21, null=False, blank=False)
    last_name = models.CharField(_('Last Name'), max_length=21)

    organization = models.CharField(
        _('Office/Organization Name'),
        max_length=255
    )

    location = models.CharField(
        _('Are you a local or foreign entity?'),
        choices=LOCATION_CHOICES,
        default=LOCATION_CHOICES.local,
        max_length=10,
    )

    email = models.EmailField(_('Email Address'), max_length=64)
    contact_number = models.CharField(_('Contact Number'), max_length=255)

    organization_type = enum.EnumField(
        OrganizationType,
        default=OrganizationType.OTHER,
        help_text=_('Organization type based on Phil-LiDAR1 Data Distribution Policy'),
        blank = True,
        null = True
    )
    org_type = models.CharField(
        _('Organization Type'),
        max_length=255,
        blank=False,
        null=False,
        default="Other",
        help_text=_('Organization type based on Phil-LiDAR1 Data Distribution Policy')
    )
    organization_other = models.CharField(
        _('If Other, please specify'),
        max_length=255,
        blank=True,
        null=True,
    )

    request_level = models.CharField(
        _('Level of Request'),
        choices=REQUEST_LEVEL_CHOICES,
        blank=True,
        null=True,
        max_length=15,
    )

    funding_source = models.CharField(
        _('Source of Funding'),
        max_length=255,
        blank=True,
        null=True
    )

    is_consultant = models.BooleanField(
        _('Consultant in behalf of another organization?'),
        default=False
    )

    # For email verification
    verification_key = models.CharField(max_length=50)

    key_created_date = models.DateTimeField(
            default=timezone.now,
            help_text=_('The date in which the verification key is sent'),
        )

    verification_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text=_('The date in which the verification key is verified'),

    )

    # For mapping an FTP folder to the datarequest and consequently to a user profile
    ftp_folder = models.CharField(
        _('FTP folder for the user account'),
        blank=True,
        null=True,
        max_length=100,
        #validators=[validators.RegexValidator(regex="^Others\/[a-zA-Z]{6,15}[0-9]{0,4}")]
        )

    class Meta:
        app_label = "datarequests"
        verbose_name = _('Profile Request')
        verbose_name_plural = _('Profile Requests')
        ordering = ('-created',)


    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        #self.status = self.STATUS.unconfirmed

    def __unicode__(self):
        return (_('{} request by {} {} {} of {}')
                .format(
                    self.status,
                    unidecode(self.first_name),
                    self.middle_name,
                    self.last_name,
                    self.organization,
                ))

    @property
    def has_verified_email(self):
        return self.verification_date is not None

    def get_absolute_url(self):
        return reverse('datarequests:profile_request_detail', kwargs={'pk': self.pk})

    def set_verification_key(self):
        self.verification_key = get_random_string(length=50)
        self.key_created_date = timezone.now()
        self.save()

    def set_status(self, status, administrator = None):
        self.status = status
        self.save()
        self.administrator = administrator
        self.save()

    def create_account(self):
        profile = None
        errors = []
        if not self.username:
            self.username = create_login_credentials(self)
            self.save()
            pprint(self.username)
        else:
            try:
                profile = LDAPBackend().populate_user(self.username)
                self.profile = profile
                self.save()
            except Exception as e:
                pprint(traceback.format_exc())
                return (False, "Account creation failed. Check /var/log/apache2/error.log for more details")

        try:
             if not self.profile:
                pprint("Creating account for "+self.username)
                dn = create_ad_account(self, self.username)
                add_to_ad_group(group_dn=settings.LIPAD_LDAP_GROUP_DN, user_dn=dn)
                profile = LDAPBackend().populate_user(self.username)

                if profile:
                    self.profile = profile
                    self.save()

                    profile.middle_name = self.middle_name
                    profile.organization = self.organization
                    profile.voice = self.contact_number
                    profile.email = self.email
                    profile.save()
                else:
                    pprint("Accout was not created")
                    raise Exception("Account not created")
             else:
                 profile.organization_type = self.organization_type
                 profile.org_type = self.org_type
                 profile.save()
        except Exception as e:
            pprint(traceback.format_exc())
            exc_name = type(e).__name__
            pprint(exc_name)
            if exc_name == "ALREADY_EXISTS":
                return (False, "This user already has an account.")
            return (False, "Account creation failed. Check /var/log/apache2/error.log for more details")

        self.join_requester_grp()

        try:
            if not self.ftp_folder:
                self.create_directory()
        except Exception as e:
            pprint(traceback.format_exc())
            return (False, "Folder creation failed, Check /var/log/apache2/error.log for more details")

        return  (True, "Account creation successful")

    def join_requester_grp(self):
        # Add account to requesters group
        group_name = "Data Requesters"
        requesters_group, created = GroupProfile.objects.get_or_create(
            title=group_name,
            slug=slugify(group_name),
            access='private',
        )

        try:
            group_member = GroupMember.objects.get(group=requesters_group, user=self.profile)
            if not group_member:
                requesters_group.join(self.profile, role='member')
        except ObjectDoesNotExist as e:
            pprint(self.profile)
            requesters_group.join(self.profile, role='member')
            #raise ValueError("Unable to add user to the group")

    def create_directory(self):
        pprint("creating user folder for "+self.username)
        create_folder.delay(self.username)
        self.ftp_folder = "Others/"+self.username
        self.save()

    def get_organization_type(self):
        return self.org_type
        #return OrganizationType.get(getattr(self,'organization_type'))

    def to_values_list(self, fields=['id','name','email','contact_number', 'organization','org_type', 'created','status','has_data_request']):
        out = []
        for f in fields:
            if f  is 'id':
                out.append(getattr(self, 'pk'))
            elif f is 'name':
                first_name = unidecode(getattr(self, 'first_name'))
                last_name = unidecode(getattr(self,'last_name'))
                out.append(first_name+" "+last_name)
            elif f is 'created':
                created = getattr(self, f)
                out.append( str(created.month) +"/"+str(created.day)+"/"+str(created.year))
            elif f == 'status update' or f == 'status changed':
                status_changed = self.status_changed
                if status_changed:
                    out.append(str(status_changed.month)+"/"+str(status_changed.day)+"/"+str(status_changed.year))
                else:
                    out.append(str(None))
            elif f == 'data_request_status':
                if self.data_request:
                    out.append(str(self.data_request.status))
                else:
                    out.append(" ")
            elif f is 'org_type' or f is 'organization_type':
                out.append(self.org_type)
            elif f is 'rejection_reason':
                out.append(str(getattr(self,'rejection_reason')))
            elif f is 'has_data_request':
                if self.data_request:
                    out.append('yes')
                else:
                    out.append('no')
            elif f is 'place_name':
                if self.data_request:
                    out.append(self.data_request.place_name)
                else:
                    out.append("NA")
            elif f is 'area_coverage':
                if self.data_request:
                    out.append(self.data_request.area_coverage)
                else:
                    out.append("NA")
            elif f is 'estimated_data_size':
                if self.data_request:
                    out.append(self.data_request.juris_data_size)
                else:
                    out.append("NA")
            else:
                val = getattr(self, f)
                if isinstance(val, unicode):
                    out.append(unidecode(val))
                else:
                    out.append(str(val))

        return out

    def send_email(self, subj, msg, html_msg, recipient=settings.LIPAD_SUPPORT_MAIL):
        text_content = msg

        html_content = html_msg

        email_subject = _(subj)

        msg = EmailMultiAlternatives(
            email_subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [recipient, ]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    def send_new_request_notif_to_admins(self, request_type="Profile"):
        text_content = email_utils.NEW_REQUEST_EMAIL_TEXT.format(
            request_type,
            settings.BASEURL + self.get_absolute_url()
        )

        html_content=email_utils.NEW_REQUEST_EMAIL_HTML.format(
            request_type,
            settings.BASEURL + self.get_absolute_url(),
            settings.BASEURL + self.get_absolute_url()
        )

        email_subj = "[LiPAD] A new request has been submitted"
        self.send_email(email_subj,text_content,html_content)

    def send_verification_email(self):
        self.set_verification_key()
        site = Site.objects.get_current()
        verification_url = (
            str(site) +
            reverse('datarequests:email_verification_confirm') +
            '?key=' + self.verification_key + '&email=' +
            urlquote(self.email)
        )
        verification_url = iri_to_uri(verification_url).replace("//", "/")

        text_content = email_utils.VERIFICATION_EMAIL_TEXT.format(
             unidecode(self.first_name),
             verification_url,
             settings.LIPAD_SUPPORT_MAIL,
         )

        html_content = email_utils.VERIFICATION_EMAIL_HTML.format(
            unidecode(self.first_name),
            verification_url,
            verification_url,
            settings.LIPAD_SUPPORT_MAIL,
            settings.LIPAD_SUPPORT_MAIL,
        )

        email_subj = _('[LiPAD] Email Confirmation')
        self.send_email(email_subj,text_content,html_content, recipient=self.email)

    def send_approval_email(self):
        site = Site.objects.get_current()
        profile_url = (
            str(site) +
            reverse('profile_detail', kwargs={'username': self.username})
        )
        profile_url = iri_to_uri(profile_url)

        text_content = email_utils.PROFILE_APPROVAL_TEXT.format(
            unidecode(self.first_name),
            self.username,
            profile_url,
            settings.LIPAD_SUPPORT_MAIL
        )

        html_content = email_utils.PROFILE_APPROVAL_HTML.format(
            unidecode(self.first_name),
            self.username,
            profile_url,
            settings.LIPAD_SUPPORT_MAIL,
            settings.LIPAD_SUPPORT_MAIL
        )

        email_subj = _('[LiPAD] Account Registration Status')
        self.send_email(email_subj,text_content,html_content, recipient=self.email)

    def send_rejection_email(self):
        additional_details = 'Additional Details: ' + str(self.additional_rejection_reason)

        text_content = email_utils.PROFILE_REJECTION_TEXT.format(
             unidecode(self.first_name),
             self.rejection_reason,
             additional_details,
             settings.LIPAD_SUPPORT_MAIL
         )

        html_content = email_utils.PROFILE_REJECTION_HTML.format(
             unidecode(self.first_name),
             self.rejection_reason,
             additional_details,
             settings.LIPAD_SUPPORT_MAIL,
             settings.LIPAD_SUPPORT_MAIL
        )

        email_subj = _('[LiPAD] Account Registration Status')
        self.send_email(email_subj,text_content,html_content, recipient=self.email)
