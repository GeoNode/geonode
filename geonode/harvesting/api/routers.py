#########################################################################
#
# Copyright (C) 2021 OSGeo
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

from rest_framework.routers import (
    DynamicRoute,
    Route,
)
from rest_framework_extensions.routers import ExtendedSimpleRouter


class ListPatchRouter(ExtendedSimpleRouter):
    """A router that allows performing PATCH requests against the `list` endpoint

    This router is used in order to provide API endpoints that respond to PATCH
    requsts against a viewset's `list` endpoint. It is useful for situations where it
    is necessary to perform a batch update of multiple resources. For a use case,
    consider the selection of which remote resources should be harvestable by the local
    GeoNode:

    - User is shown a (paginated) list of resources that are available on the remote
    service
    - User must now choose which of these harvestable resources should be harvested
    - Instead of forcing the user to make multiple PATCH requests to each harvestable
    resource's detail page in order to set the resource's `should_be_harvested`
    property, user can perform a PATCH request to
    `harvesters/{harvester-id}/harvestable-resources` and set multiple resources'
    `should_be_harvested` at the same time

    """

    routes = [
        # List route.
        Route(
            url=r"^{prefix}{trailing_slash}$",
            mapping={
                "get": "list",
                "post": "create",
                "patch": "update_list",
            },
            name="{basename}-list",
            detail=False,
            initkwargs={"suffix": "List"},
        ),
        # Dynamically generated list routes. Generated using
        # @action(detail=False) decorator on methods of the viewset.
        DynamicRoute(
            url=r"^{prefix}/{url_path}{trailing_slash}$", name="{basename}-{url_name}", detail=False, initkwargs={}
        ),
        # Detail route.
        Route(
            url=r"^{prefix}/{lookup}{trailing_slash}$",
            mapping={"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"},
            name="{basename}-detail",
            detail=True,
            initkwargs={"suffix": "Instance"},
        ),
        # Dynamically generated detail routes. Generated using
        # @action(detail=True) decorator on methods of the viewset.
        DynamicRoute(
            url=r"^{prefix}/{lookup}/{url_path}{trailing_slash}$",
            name="{basename}-{url_name}",
            detail=True,
            initkwargs={},
        ),
    ]
