# Permissions mapping
PERMISSIONS = {
    'base_addresourcebase': 'ADD_RESOURCE',
    }

# The following permissions will be filtered out when READ_ONLY mode is active
READ_ONLY_AFFECTED_PERMISSIONS = [
    'ADD_RESOURCE',
]

# Permissions on resources
VIEW_PERMISSIONS = [
    'view_resourcebase',
    'download_resourcebase',
]

ADMIN_PERMISSIONS = [
    'change_resourcebase_metadata',
    'change_resourcebase',
    'delete_resourcebase',
    'change_resourcebase_permissions',
    'publish_resourcebase',
]

LAYER_ADMIN_PERMISSIONS = [
    'change_layer_data',
    'change_layer_style'
]
