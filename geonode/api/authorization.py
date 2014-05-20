from tastypie.authorization import DjangoAuthorization
from tastypie.exceptions import Unauthorized


class GeoNodeAuthorization(DjangoAuthorization):
    """Object level API authorization based on GeoNode granular permission system"""

    def read_list(self, object_list, bundle):
        # this applies permissions preserving the queryset for future use (faceting)
        for obj in object_list:
            if not bundle.request.user.has_perm('base.view_resourcebase', obj.resourcebase_ptr):
                object_list = object_list.exclude(id__exact=obj.id)
        
        return object_list

    def read_detail(self, object_list, bundle):
        return bundle.request.user.has_perm('base.view_resourcebase', bundle.obj.resourcebase_ptr)

    def create_list(self, object_list, bundle):
        # TODO implement if needed
        raise Unauthorized()

    def create_detail(self, object_list, bundle):
        return bundle.request.user.has_perm('base.add_resourcebase', bundle.obj.resourcebase_ptr)

    def update_list(self, object_list, bundle):
        # TODO implement if needed
        raise Unauthorized()

    def update_detail(self, object_list, bundle):
        return bundle.request.user.has_perm('base.change_resourcebase', bundle.obj.resourcebase_ptr)

    def delete_list(self, object_list, bundle):
        # TODO implement if needed
        raise Unauthorized()

    def delete_detail(self, object_list, bundle):
        return bundle.request.user.has_perm('base.delete_resourcebase', bundle.obj.resourcebase_ptr)
