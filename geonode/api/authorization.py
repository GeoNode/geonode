from tastypie.authorization import DjangoAuthorization
from tastypie.exceptions import Unauthorized


class GeoNodeAuthorization(DjangoAuthorization):
    """Object level API authorization based on GeoNode granular permission system"""

    def __init__(self, *args, **kwargs):
        self.view_perm = kwargs.pop('view_perm')
        self.create_perm = kwargs.pop('create_perm')
        self.update_perm = kwargs.pop('update_perm')
        self.delete_perm = kwargs.pop('delete_perm')
        super(GeoNodeAuthorization, self).__init__(**kwargs)

    def read_list(self, object_list, bundle):
        return [i for i in object_list if bundle.request.user.has_perm(self.view_perm, i)]

    def read_detail(self, object_list, bundle):
        return bundle.request.user.has_perm(self.view_perm, bundle.obj)

    def create_list(self, object_list, bundle):
        raise Unauthorized()

    def create_detail(self, object_list, bundle):
        return bundle.request.user.has_perm(self.create_perm, bundle.obj)

    def update_list(self, object_list, bundle):
        raise Unauthorized()

    def update_detail(self, object_list, bundle):
        return bundle.request.user.has_perm(self.update_perm, bundle.obj)

    def delete_list(self, object_list, bundle):
        raise Unauthorized()

    def delete_detail(self, object_list, bundle):
        return bundle.request.user.has_perm(self.delete_perm, bundle.obj)
