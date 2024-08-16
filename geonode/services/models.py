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

from urllib.parse import urlparse, ParseResult

from django.db import models
from django.conf import settings

from django.utils.translation import gettext_lazy as _

from geonode.base.models import ResourceBase
from geonode.harvesting.models import Harvester
from geonode.layers.enumerations import GXP_PTYPES
from geonode.people.enumerations import ROLE_VALUES
from geonode.services.serviceprocessors import get_available_service_types

from . import enumerations

service_type_as_tuple = [(k, v["label"]) for k, v in get_available_service_types().items()]

logger = logging.getLogger("geonode.services")


class Service(ResourceBase):
    """Service Class to represent remote Geo Web Services"""

    type = models.CharField(max_length=10, choices=service_type_as_tuple)
    method = models.CharField(
        max_length=1,
        choices=(
            (enumerations.LOCAL, _("Local")),
            (enumerations.CASCADED, _("Cascaded")),
            (enumerations.HARVESTED, _("Harvested")),
            (enumerations.INDEXED, _("Indexed")),
            (enumerations.LIVE, _("Live")),
            (enumerations.OPENGEOPORTAL, _("OpenGeoPortal")),
        ),
    )
    # with service, version and request etc stripped off
    base_url = models.URLField(unique=True, db_index=True)
    version = models.CharField(max_length=100, null=True, blank=True)
    # Should force to slug?
    name = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    extra_queryparams = models.TextField(null=True, blank=True)
    operations = models.JSONField(default=dict, null=True, blank=True)

    # Foreign Keys

    harvester = models.ForeignKey(
        Harvester, null=True, blank=True, on_delete=models.CASCADE, related_name="service_harvester"
    )

    # Supported Capabilities

    def __str__(self):
        return str(self.name)

    @property
    def probe(self):
        if self.harvester:
            return self.harvester.remote_available
        return False

    def _get_service_url(self):
        parsed_url = urlparse(self.base_url)
        encoded_get_args = self.extra_queryparams
        _service_url = ParseResult(
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            encoded_get_args,
            parsed_url.fragment,
        )
        return _service_url.geturl()

    @property
    def service_url(self):
        return self._get_service_url()

    @property
    def ptype(self):
        # Return the gxp ptype that should be used to display layers
        return GXP_PTYPES[self.type] if self.type else None

    @property
    def service_type(self):
        # Return the gxp ptype that should be used to display layers
        return [x for x in service_type_as_tuple if x[0] == self.type][0][1]

    def get_absolute_url(self):
        return "/services/%i" % self.id

    class Meta:
        # custom permissions,
        # change and delete are standard in django-guardian
        permissions = (
            ("add_resourcebase_from_service", "Can add resources to Service"),
            ("change_resourcebase_metadata", "Can change resources metadata"),
        )


class ServiceProfileRole(models.Model):
    """
    ServiceProfileRole is an intermediate model to bind Profiles and Services and apply roles.
    """

    profiles = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    role = models.CharField(
        choices=ROLE_VALUES, max_length=255, help_text=_("function performed by the responsible party")
    )
