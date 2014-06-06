from tastypie.authorization import DjangoAuthorization
from tastypie.exceptions import Unauthorized
from guardian.shortcuts import get_objects_for_user, get_anonymous_user

anonymous_user = get_anonymous_user()
def filter_security(user, perm, obj):
        
    return user.has_perm(perm, obj.get_self_resource()) or anonymous_user.has_perm(perm, obj.get_self_resource())

class GeoNodeAuthorization(DjangoAuthorization):
    """Object level API authorization based on GeoNode granular permission system"""

    def read_list(self, object_list, bundle):
        # uses the django guardian to check permissions, then uses the id's to filter the queryset
        # The permissions cannot be checked directly on the queryset because it's polymorphic and
        # guardian does not allow to mix permissions and models

        # Include also the anonymous user.
        # TODO: improve this
        permitted_ids = (get_objects_for_user(bundle.request.user,'base.view_resourcebase').values_list('id') | 
            get_objects_for_user(anonymous_user,'base.view_resourcebase').values_list('id')).distinct()
        permitted_ids_list = [val[0] for val in permitted_ids]
        
        return object_list.filter(id__in=permitted_ids_list)

    def read_detail(self, object_list, bundle):
        return filter_security(bundle.request.user, 'view_resourcebase', bundle.obj)

    def create_list(self, object_list, bundle):
        # TODO implement if needed
        raise Unauthorized()

    def create_detail(self, object_list, bundle):
        return filter_security(bundle.request.user, 'add_resourcebase', bundle.obj)

    def update_list(self, object_list, bundle):
        # TODO implement if needed
        raise Unauthorized()

    def update_detail(self, object_list, bundle):
        return filter_security(bundle.request.user, 'change_resourcebase', bundle.obj)

    def delete_list(self, object_list, bundle):
        # TODO implement if needed
        raise Unauthorized()

    def delete_detail(self, object_list, bundle):
        return filter_security(bundle.request.user, 'delete_resourcebase', bundle.obj)
