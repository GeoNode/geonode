from tastypie.authorization import DjangoAuthorization
from tastypie.exceptions import Unauthorized
from guardian.shortcuts import get_objects_for_user


class GeoNodeAuthorization(DjangoAuthorization):
    """Object level API authorization based on GeoNode granular permission system"""

    def read_list(self, object_list, bundle):
        # uses the django guardian to check permissions, then uses the id's to filter the queryset
        # The permissions cannot be checked directly on the queryset because it's polymorphic and
        # guardian does not allow to mix permissions and models

        # TODO: improve this
        perm_id_list = [val[0] for val in get_objects_for_user(bundle.request.user,'base.view_resourcebase').values_list('id')]
        
        return object_list.filter(id__in=perm_id_list)

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
