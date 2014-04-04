from tastypie.authorization import DjangoAuthorization
from tastypie.exceptions import Unauthorized

perms = {
    'Layer': {
        'view': 'layers.view_layer',
        'add': 'layers.add_layer',
        'change': 'layers.change_layer',
        'delete': 'layers.delete_layer',
    },
    'Map': {
        'view': 'maps.view_map',
        'add': 'maps.add_map',
        'change': 'maps.change_map',
        'delete': 'maps.delete_map',
    },
    'Document': {
        'view': 'documents.view_document',
        'add': 'documents.add_document',
        'change': 'documents.change_document',
        'delete': 'documents.delete_document',
    }
}


class GeoNodeAuthorization(DjangoAuthorization):
    """Object level API authorization based on GeoNode granular permission system"""

    def read_list(self, object_list, bundle):
        # this applies permissions preserving the queryset for future use (faceting)
        for obj in object_list:
            if not bundle.request.user.has_perm(perms[obj.class_name]['view'], obj):
                object_list = object_list.exclude(id__exact=obj.id)
        
        return object_list

    def read_detail(self, object_list, bundle):
        return bundle.request.user.has_perm(perms[bundle.obj.class_name]['view'], bundle.obj)

    def create_list(self, object_list, bundle):
        # TODO implement if needed
        raise Unauthorized()

    def create_detail(self, object_list, bundle):
        return bundle.request.user.has_perm(perms[bundle.obj.class_name]['add'], bundle.obj)

    def update_list(self, object_list, bundle):
        # TODO implement if needed
        raise Unauthorized()

    def update_detail(self, object_list, bundle):
        return bundle.request.user.has_perm(perms[bundle.obj.class_name]['change'], bundle.obj)

    def delete_list(self, object_list, bundle):
        # TODO implement if needed
        raise Unauthorized()

    def delete_detail(self, object_list, bundle):
        return bundle.request.user.has_perm(perms[bundle.obj.class_name]['delete'], bundle.obj)
