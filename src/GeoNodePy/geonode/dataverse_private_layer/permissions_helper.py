"""
The permissions model between Dataverse and WorldMap is quite general.

This appplies to Viewing a layer created from a DatasetVersion:

    - DatasetVersion is public* (released):  WorldMap layer is public

    - DatasetVersion is NOT public* (released): WorldMap layer is visible only to users who can edit

"""
from django.contrib.contenttypes.models import ContentType
from geonode.maps.views import Map, MAP_LEV_NAMES

from geonode.core.models import GENERIC_GROUP_NAMES, ANONYMOUS_USERS, AUTHENTICATED_USERS, CUSTOM_GROUP_USERS, \
     GenericObjectRoleMapping, Permission, ObjectRole, UserObjectRoleMapping
from geonode.maps.models import Layer  #LEVEL_READ

import logging

logger = logging.getLogger("geonode.dataverse_private_layer.permissions_helper")



def get_layer_content_type():
    try:
        return ContentType.objects.get(name='layer')
    except ContentType.DoesNotExist:
        logger.error('The Content Type "layer" was not found in the database')
        raise ValueError('The Content Type "layer" was not found in the database')


def make_layer_private(layer):
    """
    Only allow editors of this layer view it
    """
    assert type(layer) is Layer, "layer must be a Layer object"

    layer_content_type = get_layer_content_type()

    #   Remove generic object role mappings
    #
    role_mappings = GenericObjectRoleMapping.objects.filter(object_ct=layer_content_type\
                                                        , object_id=layer.id\
                                                        )
    role_mappings.delete()

    # editors should already have distinct permissions
    #  - make sure that owner is an editor
    #
    if layer.owner is not None:
        layer.set_user_level(layer.owner, layer.LEVEL_ADMIN)

    return True


def make_layer_public(layer):
    """
    Make layer public

    Subject: Anonymous Users
    GENERIC_GROUP_NAMES = {
    ANONYMOUS_USERS: _('Anonymous Users'),
    AUTHENTICATED_USERS: _('Registered Users'),
    CUSTOM_GROUP_USERS: _(settings.CUSTOM_GROUP_NAME)
}
    """
    assert type(layer) is Layer, "layer must be a Layer object"

    layer_content_type = get_layer_content_type()

    # Public viewing parameters
    #
    basic_params = { 'object_ct' : layer_content_type\
                    , 'object_id' : layer.id\
                        }
    public_params = {
                    'subject' : ANONYMOUS_USERS\
                    , 'role' : ObjectRole.objects.get(codename=Layer.LEVEL_READ)\
                    }
    public_params.update(basic_params)

    # Do public viewing permissions already exist
    #
    if GenericObjectRoleMapping.objects.filter(**public_params).count() > 0:
        return True

    # Clear other permissions for this layer
    #
    if GenericObjectRoleMapping.objects.filter(**basic_params).count() > 0:
        GenericObjectRoleMapping.objects.filter(**basic_params).delete()

    # Add public perms
    #
    gorm = GenericObjectRoleMapping(**public_params)
    gorm.save()
    return True

"""
To privatize an Existing Layer:
```
from geonode.maps.models import Layer
from django.contrib.contenttypes.models import ContentType

# retrieve layer and content type
#
layer = Layer.objects.get(pk=4)
ct = ContentType.objects.get(name='layer')

# remove generic object role mappings
#
role_mappings = GenericObjectRoleMapping.objects.filter(object_ct=ct\
                                , object_id=layer.id\
                                )
role_mappings.delete()

# editors should already have distinct permissions
#  - make sure that owner is an editor
#
if layer.owner is not None:
    layer.set_user_level(layer.owner, layer.LEVEL_ADMIN)
```


            
  * Status is captured in object DataverseLayerMetadata.dataset_is_public  (BooleanField)

Basic information on WorldMap side:

    (1) ajax_layer_permissions_by_email(request, layername)

    (2) ajax_layer_permissions(request, layername, True)
            def ajax_layer_permissions(request, layername, use_email=False)
                permission_spec = json.loads(request.raw_post_data)
                set_layer_permissions(layer, permission_spec, use_email)

    (3) set_layer_permissions(layer, perm_spec, use_email = False)
        
    
    -> perm_spec: only users who can edit:
    
        {"anonymous":"_none" 
    	, "authenticated":"_none" 
    	, "customgroup":"_none" 
		,"users":[
		            ["pete@malinator.com","layer_admin"]
		            ,["r@r.com","layer_admin"]
		        ]
		}

    -> perm_spec: Anyone:
                permissions: {"authenticated": "_none", "users": [["pete@malinator.com", "layer_admin"], ["r@r.com", "layer_admin"]], "owner_email": "r@r.com", "levels": [["_none", "No Permissions"], ["layer_readonly", "Read Only"], ["layer_readwrite", "Read/Write"], ["layer_admin", "Administrative"]], "names": [["pete@malinator.com", "pete"], ["r@r.com", "rp"]], "anonymous": "layer_readonly", "owner": "rp", "customgroup": "_none"},
                
        {"anonymous":"layer_readonly"
		,"authenticated":"_none"
		,"customgroup":"_none"
		,"users":[
		            ["pete@malinator.com","layer_admin"]
		            ,["r@r.com","layer_admin"]
		        ]
		}
		
	-> perm_spec: Any registered users
	
	    {"anonymous":"_none"
		,"authenticated":"layer_readonly"
		,"customgroup":"layer_readonly"
		,"users":[
		            ["pete@malinator.com","layer_admin"]
		            ,["r@r.com","layer_admin"]
		        ]
		}
		
From maps views:
		LAYER_LEV_NAMES = {
            Layer.LEVEL_NONE  : _('No Permissions'),
            Layer.LEVEL_READ  : _('Read Only'),
            Layer.LEVEL_WRITE : _('Read/Write'),
            Layer.LEVEL_ADMIN : _('Administrative')
        }
		
"""

"""
$ python manage.py shell --settings=geonode.settings

from geonode.maps.models import *
from geonode.maps.views import _perms_info_email, LAYER_LEV_NAMES

l = Layer.objects.get(pk=4)

_perms_info_email(l, LAYER_LEV_NAMES)

"""
