#########################################################################
#
# Copyright (C) 2024 OSGeo
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
from abc import ABC

from geonode.security.utils import AdvancedSecurityWorkflowManager


class BasePermissionsHandler(ABC):
    """
    Abstract permissions handler.
    This is the base class, all the permissions instances should
    inherit from this class.
    All the flows that touches the permissions will use this class
    (example advanced workflow)
    """

    def __str__(self):
        return f"{self.__module__}.{self.__class__.__name__}"

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def fixup_perms(instance, perms_payload, include_virtual, *args, **kwargs):
        return perms_payload

    @staticmethod
    def get_perms(instance, perms_payload, user, include_virtual, *args, **kwargs):
        """
        By default we dont provide any additional perms
        """
        return perms_payload


class AdvancedWorkflowPermissionsHandler(BasePermissionsHandler):
    """
    Handler that takes care of adjusting the permissions for the advanced workflow
    """

    @staticmethod
    def fixup_perms(instance, perms_payload, include_virtual=True, *args, **kwargs):
        # Fixup Advanced Workflow permissions
        return AdvancedSecurityWorkflowManager.get_permissions(
            instance.uuid,
            instance=instance,
            permissions=perms_payload,
            created=kwargs.get("created"),
            approval_status_changed=kwargs.get("approval_status_changed"),
            group_status_changed=kwargs.get("group_status_changed"),
        )
