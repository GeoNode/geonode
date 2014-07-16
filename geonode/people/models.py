# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.db import models
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse

from django.contrib.auth.models import AbstractUser

from taggit.managers import TaggableManager

from geonode.base.enumerations import COUNTRIES


class Profile(AbstractUser):

    """Fully featured Geonode user"""

    organization = models.CharField(
        _('Organization Name'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('name of the responsible organization'))
    profile = models.TextField(_('Profile'), null=True, blank=True)
    position = models.CharField(
        _('Position Name'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('role or position of the responsible person'))
    voice = models.CharField(_('Voice'), max_length=255, blank=True, null=True, help_text=_(
        'telephone number by which individuals can speak to the responsible organization or individual'))
    fax = models.CharField(_('Facsimile'), max_length=255, blank=True, null=True, help_text=_(
        'telephone number of a facsimile machine for the responsible organization or individual'))
    delivery = models.CharField(
        _('Delivery Point'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('physical and email address at which the organization or individual may be contacted'))
    city = models.CharField(
        _('City'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('city of the location'))
    area = models.CharField(
        _('Administrative Area'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('state, province of the location'))
    zipcode = models.CharField(
        _('Postal Code'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('ZIP or other postal code'))
    country = models.CharField(
        choices=COUNTRIES,
        max_length=3,
        blank=True,
        null=True,
        help_text=_('country of the physical address'))
    keywords = TaggableManager(_('keywords'), blank=True, help_text=_(
        'commonly used word(s) or formalised word(s) or phrase(s) used to describe the subject \
            (space or comma-separated'))

    def get_absolute_url(self):
        return reverse('profile_detail', args=[self.username, ])

    def __unicode__(self):
        return u"%s" % (self.username)

    def class_name(value):
        return value.__class__.__name__

    USERNAME_FIELD = 'username'


def get_anonymous_user_instance(Profile):
    return Profile(username='AnonymousUser')
