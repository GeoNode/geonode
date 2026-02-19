#########################################################################
#
# Copyright (C) 2020 OSGeo
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
from dynamic_rest.viewsets import DynamicModelViewSet
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter

from django.conf import settings
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter, AdvertisedFilter
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.base.api.permissions import UserHasPerms
from geonode.base.api.views import ApiPresetsInitializer
from geonode.geoapps.models import GeoApp
from geonode.metadata.multilang.views import MultiLangViewMixin
from geonode.resource.utils import resolve_resource_owner


from .serializers import GeoAppSerializer
from .permissions import GeoAppPermissionsFilter

import logging


logger = logging.getLogger(__name__)


class GeoAppViewSet(ApiPresetsInitializer, MultiLangViewMixin, DynamicModelViewSet):
    """
    API endpoint that allows geoapps to be viewed or edited.
    """

    http_method_names = ["get", "patch", "post", "put"]
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        UserHasPerms(perms_dict={"default": {"POST": ["base.add_resourcebase"]}}),
    ]
    filter_backends = [
        DynamicFilterBackend,
        DynamicSortingFilter,
        DynamicSearchFilter,
        AdvertisedFilter,
        ExtentFilter,
        GeoAppPermissionsFilter,
    ]
    queryset = GeoApp.objects.all().order_by("-created")
    serializer_class = GeoAppSerializer
    pagination_class = GeoNodeApiPagination

    def perform_create(self, serializer):
        """
        The owner is not passed from the FE
        so we force the request.user to be the owner
        in creation
        """
        resolved_owner = resolve_resource_owner(self.request.user)
        instance = serializer.save(owner=resolved_owner)
        if getattr(settings, "AUTO_ASSIGN_RESOURCE_OWNERSHIP_TO_ADMIN", False):
            instance.set_default_permissions(owner=resolved_owner, created=True, initial_user=self.request.user)
        return instance
