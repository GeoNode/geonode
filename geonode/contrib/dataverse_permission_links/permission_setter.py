"""
For a Dataverse-created map, check if additional users
should have edit permissions
"""
from django.shortcuts import get_object_or_404

from geonode.maps.models import Layer
from geonode.core.models import PermissionLevelMixin

from geonode.contrib.dataverse_permission_links.models import DataversePermissionLink


class PermissionLinker(object):
    """
    For a Dataverse-created map, check if additional users
    should have edit permissions
    """

    def __init__(self, layer_name, dataverse_username):
        """
        layer_name: e.g. "geonode:j_cbg_annual_census_bloc_1z"
        dv_username: from DatavereLayerMetadata.dv_username
        """
        self.layer_name = layer_name
        self.dv_username = dataverse_username

        # Most layers will not be linked to additional
        # WorldMap credentials
        self.was_layer_linked = False

        # Hold error messages
        self.has_error = False
        self.error_message = None

        # If appropriate, link the layer
        self.sanity_check()


    def add_error(self, err_msg):
        """Add error message"""
        self.has_error = True
        self.error_message = err_msg

    def sanity_check(self):
        """Check for null values"""
        if self.layer_name is None:
            self.add_error("layer_name cannot be None")
            return False

        if self.dv_username is None:
            self.add_error("dv_username cannot be None")
            return False

        return True

    def link_layer(self):
        if self.has_error:
            return False

        # (1) Retrieve the PermissionLink(s)
        #
        filter_params = dict(dataverse_username=self.dv_username,
                          is_active=True)
        perm_links = DataversePermissionLink.objects.filter(**filter_params)
        if len(perm_links) == 0:
            # Most times, there are no links, this is OK
            return True

        # (2) Retrieve the Map Layer
        #
        try:
            map_obj = Layer.objects.get(typename=self.layer_name)
        except Layer.DoesNotExist:
            self.add_error("The layer was not found: %s" % self.layer_name)
            return False

        # (3) Give edit permissions to each associated WorldMap user
        #
        for perm_link in perm_links:
            # set to admin level.
            # "set_user_level" clears perms before setting them.  It doesn't allow dupes
            map_obj.set_user_level(perm_link.worldmap_user, Layer.LEVEL_ADMIN)

        self.was_layer_linked = True
        return True

"""
from geonode.contrib.dataverse_permission_links.permission_setter import PermissionLinker

layer_name = 'geonode:starbucks_u_c2'
dataverse_username = 'dv_bari'

pl = PermissionLinker(layer_name, dataverse_username)
if not pl.link_layer():
    print pl.error_message
else:
    print 'worked!'

"""
