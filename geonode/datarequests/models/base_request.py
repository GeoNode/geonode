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
from django_auth_ldap.backend import LDAPBackend, ldap_error

from model_utils import Choices
from model_utils.models import TimeStampedModel, StatusModel

from geonode.cephgeo.models import UserJurisdiction
from geonode.datarequests.utils import create_login_credentials, create_ad_account, add_to_ad_group
from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.people.models import OrganizationType, Profile

from pprint import pprint
from unidecode import unidecode

import traceback

from django.conf import settings as local_settings


class LipadOrgType(models.Model):
    val = models.CharField(_('Value'), max_length=100)
    display_val = models.CharField(_('Display'), max_length=100)
    category = models.CharField(_('Sub'), max_length=100, null=True)

    class Meta:
        app_label = "datarequests"

    def __unicode__(self):
        return (_('{}').format(self.val,))

class BaseRequest(TimeStampedModel, StatusModel):

    STATUS = Choices(
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('cancelled', _('Cancelled')),
        ('rejected', _('Rejected')),
        ('unconfirmed',_('Unconfirmed Email')),
    )

    profile = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    administrator = models.ForeignKey(
        Profile,
        null=True,
        blank=True,
        related_name="admin+"
    )

    rejection_reason = models.CharField(
        _('Reason for Rejection'),
        blank=True,
        null=True,
        max_length=100,
    )

    additional_remarks = models.TextField(
        blank = True,
        null = True,
        help_text= _('Additional remarks by an administrator'),
    )

    additional_rejection_reason = models.TextField(
        _('Additional details about rejection'),
        blank=True,
        null=True,
        )

    class Meta:
        abstract = True
        app_label = "datarequests"

class RequestRejectionReason(models.Model):
    reason = models.CharField(_('Reason for rejection'), max_length=100)

    class Meta:
        app_label = "datarequests"

    def __unicode__(self):
        return (_('{}').format(self.reason,))
