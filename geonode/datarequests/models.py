from django.db import models
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext as _
from django.utils.encoding import iri_to_uri
from django.utils.http import urlquote
from django_enumfield import enum
from django.core import validators
from django_auth_ldap.backend import LDAPBackend

from model_utils import Choices
from model_utils.models import TimeStampedModel

from geonode.cephgeo.models import UserJurisdiction
from geonode.groups.models import GroupProfile, GroupMember
from geonode.layers.models import Layer
from geonode.documents.models import Document
from geonode.people.models import OrganizationType, Profile
from geonode.utils import resolve_object
from geonode.base.models import ResourceBase
from geonode.tasks.mk_folder import create_folder

from pprint import pprint

import traceback

import geonode.settings as local_settings

from .utils import create_login_credentials, create_ad_account, add_to_ad_group

class DataRequestProfile(TimeStampedModel):

    # Choices that will be used for fields
    LOCATION_CHOICES = Choices(
        ('local', _('Local')),
        ('foreign', _('Foreign')),
    )

    DATA_TYPE_CHOICES = Choices(
        ('interpreted', _('Interpreted')),
        ('raw', _('Raw')),
        ('processed', _('Processed')),
        ('other', _('Other')),
    )

    REQUEST_STATUS_CHOICES = Choices(
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('cancelled', _('Cancelled')),
        ('rejected', _('Rejected')),
        ('unconfirmed',_('Unconfirmed Email')),
    )

    REQUESTER_TYPE_CHOICES = Choices(
        ('commercial', _('Commercial Requester')),
        ('noncommercial', _('Non-Commercial Requester')),
        ('academe', _('Academe Requester')),
    )

    DATASET_USE_CHOICES = Choices(
        ('commercial', _('Commercial')),
        ('noncommercial', _('Non-commercial')),
    )

    # ===============

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

    profile = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    username = models.CharField(
        _('User name'),
        max_length=50,
        null=True,
        blank=True,
    )

    # jurisdiction_shapefile = models.ForeignKey(Layer, null=False, blank=False)
    jurisdiction_shapefile = models.ForeignKey(Layer, null=True, blank=True)

    request_status = models.CharField(
        _('Status of Data Request'),
        choices=REQUEST_STATUS_CHOICES,
        default=REQUEST_STATUS_CHOICES.unconfirmed,
        max_length=12,
        null=True,
        blank=True,
    )

    first_name = models.CharField(_('First Name'), max_length=100)
    middle_name = models.CharField(_('Middle Name'), max_length=100)
    last_name = models.CharField(_('Last Name'), max_length=100)

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
    email = models.EmailField(_('Email Address'), max_length=50)
    contact_number = models.CharField(_('Contact Number'), max_length=255)
    project_summary = models.TextField(_('Summary of Project/Program'))
    data_type_requested = models.CharField(
        _('Type of Data Requested'),
        choices=DATA_TYPE_CHOICES,
        default=DATA_TYPE_CHOICES.processed,
        max_length=15,
    )
    """
    data_set = models.CharField(
        _('Data/Data Set Subject to License'),
        max_length=100,
    )
    area_coverage = models.DecimalField(
        _('Area of Coverage'),
        max_digits=30,
        decimal_places=4,
        help_text=_('Sqr KMs'),
    )
    data_resolution = models.PositiveIntegerField(
        _('Data Resolution'),
        help_text=_('pixels per inch'),
    )
    """

    purpose = models.TextField(_('Purpose of Data'))
    intended_use_of_dataset = models.CharField(
        _('Intended Use of Dataset'),
        choices=DATASET_USE_CHOICES,
        default=DATASET_USE_CHOICES.commercial,
        max_length=15,
    )
    organization_type = enum.EnumField(
        OrganizationType,
        default=OrganizationType.OTHER,
        help_text=_('Organization type based on Phil-LiDAR1 Data Distribution Policy')
    )
    request_level = models.CharField(
        _('Level of Request'),
        choices=REQUEST_LEVEL_CHOICES,
        blank=True,
        max_length=15,
    )
    funding_source = models.CharField(
        _('Source of Funding'),
        max_length=255,
        blank=True,
    )
    is_consultant = models.BooleanField(
        _('Consultant in behalf of another organization?'),
        default=False
    )
    rejection_reason = models.CharField(
        _('Reason for Rejection'),
        blank=True,
        null=True,
        max_length=100,
    )
    additional_rejection_reason = models.TextField(
        _('Additional details about rejection'),
        blank=True,
        null=True,
        )

    #For request letter
    request_letter= models.ForeignKey(Document, null=True, blank=True)

    # For email verification
    verification_key = models.CharField(max_length=50)
    key_created_date = models.DateTimeField(
            default=timezone.now,
            help_text=_('The date in which the verification key is sent'),
        )
    date = models.DateTimeField(
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

    administrator = models.ForeignKey(
        Profile,
        null=True,
        blank=True,
        related_name="+"
    )

    action_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text=_('The date and time this data request was approved or rejected'),
    )

    class Meta:
        verbose_name = _('Data Request Profile')
        verbose_name_plural = _('Data Request Profiles')
        ordering = ('-created',)

    def __unicode__(self):
        return (_('{} request by {} {} {} of {}')
                .format(
                    self.request_status,
                    self.first_name,
                    self.middle_name,
                    self.last_name,
                    self.organization,
                ))

    @property
    def has_verified_email(self):
        return self.date is not None

    def get_absolute_url(self):
        return reverse('datarequests:data_request_profile', kwargs={'pk': self.pk})

    def set_verification_key(self):
        self.verification_key = get_random_string(length=50)
        self.key_created_date = timezone.now()
        self.save()

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
        pprint(verification_url)

        text_content = """
         Dear <strong>{}</strong>,

        Please paste the following URL in your browser to verify your email and complete your Data Request Registration.
        {}

        For inquiries, you can contact us as at {}.

        Regards,
        LiPAD Team
         """.format(
             self.first_name,
             verification_url,
             local_settings.LIPAD_SUPPORT_MAIL,
         )

        html_content = """
        <p>Dear <strong>{}</strong>,</p>

       <p>Please click on the following link to verify your email and complete your Data Request Registration.</p>
       <p><a rel="nofollow" target="_blank" href="{}">{}</a></p>
       <p>For inquiries, you can contact us as at <a href="mailto:{}" target="_top">{}</a></p>
       </br>
        <p>Regards,</p>
        <p>LiPAD Team</p>
        """.format(
            self.first_name,
            verification_url,
            verification_url,
            local_settings.LIPAD_SUPPORT_MAIL,
            local_settings.LIPAD_SUPPORT_MAIL,
        )

        email_subject = _('[LiPAD] Email Confirmation')

        msg = EmailMultiAlternatives(
            email_subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [self.email, ]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()


    def send_new_request_notif_to_admins(self):
        site = Site.objects.get_current()
        data_request_url = (
            str(site) + self.get_absolute_url()
        )

        text_content = """
        Hi,

        A new data request has been submitted by {} {}. You can view the data request profile using the following link:
        {}
        """.format(
            self.first_name,
            self.last_name,
            data_request_url,
        )

        html_content = """
        <p>Hi,</p>

        <p>A new data request has been submitted by {} {}. You can view the data request profile using the following link:</p>
        <p><a rel="nofollow" target="_blank" href="{}">{}</a></p>

        """.format(
            self.first_name,
            self.last_name,
            data_request_url,
            data_request_url,
        )

        email_subject = _('[LiPAD] New Data Request Registration Profile')

        email_reciepients = Profile.objects.filter(
                                is_superuser=True
                            ).values_list('email', flat=True)

        msg = EmailMultiAlternatives(
            email_subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            email_reciepients
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()


    def send_account_rejection_email(self):

        additional_details = 'Additional Details: ' + str(self.additional_rejection_reason)

        text_content = """
         Dear {},

        Your account registration for LiPAD was not approved.
        Reason: {}
        {}

        If you have further questions, you can contact us as at {}.

        Regards,
        LiPAD Team
         """.format(
             self.first_name,
             self.rejection_reason,
             additional_details,
             local_settings.LIPAD_SUPPORT_MAIL,
         )

        html_content = """
        <p>Dear <strong>{}</strong>,</p>

       <p>Your account registration for LiPAD was not approved.</p>
       <p>Reason: {} <br/>
       {}</p>
       <p>If you have further questions, you can contact us as at <a href="mailto:{}" target="_top">{}</a></p>
       </br>
        <p>Regards,</p>
        <p>LiPAD Team</p>
        """.format(
             self.first_name,
             self.rejection_reason,
             additional_details,
             local_settings.LIPAD_SUPPORT_MAIL,
             local_settings.LIPAD_SUPPORT_MAIL
        )

        email_subject = _('[LiPAD] Account Registration Status')

        msg = EmailMultiAlternatives(
            email_subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [self.email, ]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    def send_request_rejection_email(self):

        additional_details = 'Additional Details: ' + str(self.additional_rejection_reason)

        text_content = """
        Dear {},

        Your data request for LiPAD was not approved.
        Reason: {}
        {}

        If you have further questions, you can contact us as at {}.

        Regards,
        LiPAD Team
         """.format(
             self.first_name,
             self.rejection_reason,
             additional_details,
             local_settings.LIPAD_SUPPORT_MAIL,
         )

        html_content = """
        <p>Dear <strong>{}</strong>,</p>

       <p>Your data request for LiPAD was not approved.</p>
       <p>Reason: {} <br/>
       {}</p>
       <p>If you have further questions, you can contact us as at <a href="mailto:{}" target="_top">{}</a></p>
       </br>
        <p>Regards,</p>
        <p>LiPAD Team</p>
        """.format(
             self.first_name,
             self.rejection_reason,
             additional_details,
             local_settings.LIPAD_SUPPORT_MAIL,
             local_settings.LIPAD_SUPPORT_MAIL
        )

        email_subject = _('[LiPAD] Data Request Status')

        msg = EmailMultiAlternatives(
            email_subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [self.email, ]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    def create_account(self):
        uname = create_login_credentials(self)
        pprint("Creating account for "+uname)
        dn = create_ad_account(self, uname)
        if dn is not False:

            add_to_ad_group(group_dn=settings.LIPAD_LDAP_GROUP_DN, user_dn=dn)

            profile = LDAPBackend().populate_user(uname)
            profile.organization_type = self.organization_type
            profile.save()
            if profile is None:
                pprint("Account was not created")
                raise Http404

            self.update_profile_details(uname=uname, profile = profile)

        else:
            raise Http404

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
            requesters_group.join(self.profile, role='member')
            #raise ValueError("Unable to add user to the group")


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

    def update_profile_details(self, uname="",profile=None):
        # Link data request to profile and updating other fields of the request
        self.username = uname
        self.profile = profile
        self.ftp_folder = "Others/"+uname
        self.save()

    def create_directory(self):
        pprint("creating user folder for "+self.username)
        create_folder.delay(self.username)

    def set_approved(self, is_new_acc):
        self.request_status = 'approved'
        self.action_date = timezone.now()
        self.save()

        if is_new_acc:
            self.send_account_approval_email(self.username, self.ftp_folder)
        else:
            self.send_request_approval_email(self.username)


    def send_account_approval_email(self, username, directory):

        site = Site.objects.get_current()
        profile_url = (
            str(site) +
            reverse('profile_detail', kwargs={'username': username})
        )
        profile_url = iri_to_uri(profile_url)

        text_content = """
        Dear {},

        Your account registration for LiPAD was approved.
        You will now be able to log in using the following log-in credentials:
        username: {}

        Before you are able to login to LiPAD, visit first https://ssp.dream.upd.edu.ph/?action=sendtoken and follow the instructions to reset a password for your account.

        You will be able to edit your account details by logging in and going to the following link:
        {}

        If you have any questions, you can contact us as at {}.

        Regards,
        LiPAD Team
         """.format(
             self.first_name,
             username,
             directory,
             profile_url,
             local_settings.LIPAD_SUPPORT_MAIL
         )

        html_content = """
        <p>Dear <strong>{}</strong>,</p>

       <p>Your account registration for LiPAD was approved! You will now be able to log in using the following log-in credentials:</p>
       username: <strong>{}</strong><br/>
       </br>
       <p>Before you are able to login to LiPAD, visit first https://ssp.dream.upd.edu.ph/?action=sendtoken and follow the instructions to reset a password for your account</p></br>
       <p>You will be able to edit your account details by logging in and going to the following link:</p>
       {}
       </br>
       <p>If you have any questions, you can contact us as at <a href="mailto:{}" target="_top">{}</a></p>
       </br>
        <p>Regards,</p>
        <p>LiPAD Team</p>
        """.format(
             self.first_name,
             username,
             directory,
             profile_url,
             local_settings.LIPAD_SUPPORT_MAIL,
             local_settings.LIPAD_SUPPORT_MAIL
         )

        email_subject = _('[LiPAD] Account Registration Status')

        msg = EmailMultiAlternatives(
            email_subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [self.email, ]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    def send_request_approval_email(self, username):
        site = Site.objects.get_current()
        profile_url = (
            str(site) +
            reverse('profile_detail', kwargs={'username': username})
        )
        profile_url = iri_to_uri(profile_url)

        text_content = """
        Dear {},

        Your current data request for LiPAD was approved.

        If you have any questions, you can contact us as at {}.

        Regards,
        LiPAD Team
         """.format(
             self.first_name,
             local_settings.LIPAD_SUPPORT_MAIL
         )

        html_content = """
        <p>Dear <strong>{}</strong>,</p>

       <p>Your current data request in LiPAD was approved.
       </br>
       <p>If you have any questions, you can contact us as at <a href="mailto:{}" target="_top">{}</a></p>
       </br>
        <p>Regards,</p>
        <p>LiPAD Team</p>
        """.format(
             self.first_name,
             local_settings.LIPAD_SUPPORT_MAIL,
             local_settings.LIPAD_SUPPORT_MAIL
         )

        email_subject = _('[LiPAD] Data Request Status')

        msg = EmailMultiAlternatives(
            email_subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [self.email, ]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()


class RequestRejectionReason(models.Model):
    reason = models.CharField(_('Reason for rejection'), max_length=100)

    def __unicode__(self):
        return (_('{}').format(self.reason,))
