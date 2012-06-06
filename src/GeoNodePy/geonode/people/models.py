# -*- coding: UTF-8 -*-
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import signals
from django.utils.translation import ugettext as _

from django.contrib.auth.models import User

from idios.models import ProfileBase, create_profile

from geonode.maps.enumerations import COUNTRIES

CONTACT_FIELDS = [
    "name",
    "organization",
    "position",
    "voice",
    "facsimile",
    "delivery_point",
    "city",
    "administrative_area",
    "postal_code",
    "country",
    "email",
    "role"
]


class Contact(ProfileBase):
    name = models.CharField(_('Individual Name'), max_length=255, blank=True, null=True)
    organization = models.CharField(_('Organization Name'), max_length=255, blank=True, null=True)
    profile = models.TextField(_('Profile'), null=True, blank=True)
    position = models.CharField(_('Position Name'), max_length=255, blank=True, null=True)
    voice = models.CharField(_('Voice'), max_length=255, blank=True, null=True)
    fax = models.CharField(_('Facsimile'),  max_length=255, blank=True, null=True)
    delivery = models.CharField(_('Delivery Point'), max_length=255, blank=True, null=True)
    city = models.CharField(_('City'), max_length=255, blank=True, null=True)
    area = models.CharField(_('Administrative Area'), max_length=255, blank=True, null=True)
    zipcode = models.CharField(_('Postal Code'), max_length=255, blank=True, null=True)
    country = models.CharField(choices=COUNTRIES, max_length=3, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def clean(self):
        # the specification says that either name or organization should be provided
        valid_name = (self.name != None and self.name != '')
        valid_organization = (self.organization != None and self.organization !='')
        if not (valid_name or valid_organization):
            raise ValidationError('Either name or organization should be provided')

    def get_absolute_url(self):
        return ('profile_detail', (), { 'username': self.user.username })
    get_absolute_url = models.permalink(get_absolute_url)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.organization)

def create_user_profile(instance, sender, created, **kwargs):
    try:
        profile = Contact.objects.get(user=instance)
    except Contact.DoesNotExist:
        profile = Contact(user=instance)
        profile.name = instance.username
        profile.save()

# Remove the idios create_profile handler, which interferes with ours.
signals.post_save.disconnect(create_profile, sender=User)
signals.post_save.connect(create_user_profile, sender=User)
