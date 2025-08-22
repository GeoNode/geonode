from django.contrib.auth.backends import BaseBackend
from geonode.security.registry import permissions_registry


class PermissionsRegistryAuthBackend(BaseBackend):

    def has_perm(self, user_obj, perm, obj=None):
        if obj is None:
            return False
        # Custom permission logic
        return perm in permissions_registry\
            .user_has_perm(user_obj, instance=obj, perm=perm.split(".")[-1])
