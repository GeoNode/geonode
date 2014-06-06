from tastypie.authorization import DjangoAuthorization
from tastypie.exceptions import Unauthorized

from geonode.security.views import filter_object_security, filter_queryset_security


class GeoNodeAuthorization(DjangoAuthorization):
    """Object level API authorization based on GeoNode granular permission system"""

    def read_list(self, object_list, bundle):
        return filter_queryset_security(bundle.request.user, 'base.view_resourcebase', object_list)

    def read_detail(self, object_list, bundle):
        return filter_object_security(bundle.request.user, 'view_resourcebase', bundle.obj)

    def create_list(self, object_list, bundle):
        # TODO implement if needed
        raise Unauthorized()

    def create_detail(self, object_list, bundle):
        return filter_object_security(bundle.request.user, 'add_resourcebase', bundle.obj)

    def update_list(self, object_list, bundle):
        # TODO implement if needed
        raise Unauthorized()

    def update_detail(self, object_list, bundle):
        return filter_object_security(bundle.request.user, 'change_resourcebase', bundle.obj)

    def delete_list(self, object_list, bundle):
        # TODO implement if needed
        raise Unauthorized()

    def delete_detail(self, object_list, bundle):
        return filter_object_security(bundle.request.user, 'delete_resourcebase', bundle.obj)
