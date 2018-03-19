# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
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

import logging
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from geonode.base.models import ResourceBase
from geonode.people.enumerations import ROLE_VALUES
from urlparse import urljoin

from . import enumerations

logger = logging.getLogger("geonode.services")


class Service(ResourceBase):
    """Service Class to represent remote Geo Web Services"""

    type = models.CharField(
        max_length=6,
        choices=(
            (enumerations.AUTO, _('Auto-detect')),
            (enumerations.OWS, _('Paired WMS/WFS/WCS')),
            (enumerations.WMS, _('Web Map Service')),
            (enumerations.CSW, _('Catalogue Service')),
            (enumerations.REST, _('ArcGIS REST Service')),
            (enumerations.OGP, _('OpenGeoPortal')),
            (enumerations.HGL, _('Harvard Geospatial Library')),
            (enumerations.GN_WMS, _('GeoNode (Web Map Service)')),
            (enumerations.GN_CSW, _('GeoNode (Catalogue Service)')),
        )
    )
    method = models.CharField(
        max_length=1,
        choices=(
            (enumerations.LOCAL, _('Local')),
            (enumerations.CASCADED, _('Cascaded')),
            (enumerations.HARVESTED, _('Harvested')),
            (enumerations.INDEXED, _('Indexed')),
            (enumerations.LIVE, _('Live')),
            (enumerations.OPENGEOPORTAL, _('OpenGeoPortal'))
        )
    )
    # with service, version and request etc stripped off
    base_url = models.URLField(
        unique=True,
        db_index=True
    )
    proxy_base = models.URLField(
        null=True,
        blank=True
    )
    version = models.CharField(
        max_length=10,
        null=True,
        blank=True
    )
    # Should force to slug?
    name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True
    )
    description = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    online_resource = models.URLField(
        False,
        null=True,
        blank=True
    )
    fees = models.CharField(
        max_length=1000,
        null=True,
        blank=True
    )
    access_constraints = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    connection_params = models.TextField(
        null=True,
        blank=True
    )
    username = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    password = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    api_key = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    workspace_ref = models.URLField(
        False,
        null=True,
        blank=True
    )
    store_ref = models.URLField(
        null=True,
        blank=True
    )
    resources_ref = models.URLField(
        null=True,
        blank=True
    )
    profiles = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ServiceProfileRole'
    )
    created = models.DateTimeField(
        auto_now_add=True
    )
    last_updated = models.DateTimeField(
        auto_now=True
    )
    first_noanswer = models.DateTimeField(
        null=True,
        blank=True
    )
    noanswer_retries = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    external_id = models.IntegerField(
        null=True,
        blank=True
    )
    parent = models.ForeignKey(
        'services.Service',
        null=True,
        blank=True,
        related_name='service_set'
    )

    # Supported Capabilities

    def __unicode__(self):
        return self.name

    @property
    def service_url(self):
        service_url = self.base_url if not self.proxy_base else urljoin(
            settings.SITEURL, reverse('service_proxy', args=[self.id]))
        return service_url

    @property
    def ptype(self):
        # Return the gxp ptype that should be used to display layers
        return enumerations.GXP_PTYPES[self.type]

    def get_absolute_url(self):
        return '/services/%i' % self.id


class ServiceProfileRole(models.Model):

    """
    ServiceProfileRole is an intermediate model to bind Profiles and Services and apply roles.
    """
    profiles = models.ForeignKey(settings.AUTH_USER_MODEL)
    service = models.ForeignKey(Service)
    role = models.CharField(choices=ROLE_VALUES, max_length=255, help_text=_(
        'function performed by the responsible party'))


class HarvestJob(models.Model):
    service = models.ForeignKey(Service)
    resource_id = models.CharField(max_length=255)
    status = models.CharField(
        choices=(
            (enumerations.QUEUED, enumerations.QUEUED),
            (enumerations.CANCELLED, enumerations.QUEUED),
            (enumerations.IN_PROCESS, enumerations.IN_PROCESS),
            (enumerations.PROCESSED, enumerations.PROCESSED),
            (enumerations.FAILED, enumerations.FAILED),
        ),
        default=enumerations.QUEUED,
        max_length=15,
    )
    details = models.TextField(null=True, blank=True, default=_("Resource is queued"))

    def update_status(self, status, details=""):
        self.status = status
        self.details = details
        self.save()
