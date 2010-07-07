from django.contrib.auth.backends import ModelBackend
from django.contrib.contenttypes.models import ContentType 
from geonode.core.models import *

class GranularBackend(ModelBackend):
    """
    A granular permissions backend that supports row-level 
    user permissions. 
    """
    
    supports_object_permissions = True
    supports_anonymous_user = True

    def get_group_permissions(self, user_obj, obj=None):
        """
        Returns a set of permission strings that this user has through his/her
        groups.
        """
        if obj is None:
            return ModelBackend.get_group_permissions(self, user_obj)
        else:
            return set() # not implemented

    def get_all_permissions(self, user_obj, obj=None):
        """
        """
        
        if obj is None:
            return ModelBackend.get_all_permissions(self, user_obj)
        else:
            if not hasattr(user_obj, '_obj_perm_cache'):
                # TODO: this cache should really be bounded.
                # repoze.lru perhaps?
                user_obj._obj_perm_cache = dict()
            try:
                obj_key = self._cache_key_for_obj(obj)
                return user_obj._obj_perm_cache[obj_key]
            except KeyError:
                all_perms = ['%s.%s' % p for p in self._get_all_obj_permissions(user_obj, obj)]
                user_obj._obj_perm_cache[obj_key] = all_perms
                return all_perms

    def _cache_key_for_obj(self, obj):
        model = obj.__class__
        opts = model._meta
        while opts.proxy:
            model = opts.proxy_for_model
            opts = model._meta
        key = (opts.app_label, opts.object_name.lower(), obj.id)
        return key
    
    def _get_generic_obj_permissions(self, user_obj, obj, ct=None):
        perms = set()
        
        generic_roles = [ANONYMOUS_USERS]
        if not user_obj.is_anonymous():
            generic_roles.append(AUTHENTICATED_USERS)

        if ct is None:
            ct = ContentType.objects.get_for_model(obj)
        
        perms = Permission.objects.filter(rowlevel_generic__subject__in=generic_roles,
                                          rowlevel_generic__object_ct=ct,
                                          rowlevel_generic__object_id=obj.id).values_list('content_type__app_label', 'codename').order_by()
        
        return perms
        
    def _get_all_obj_permissions(self, user_obj, obj, ct=None):
        """
        get all permissions for user in the context of ob (not cached)
        """
        if ct is None: 
            ct = ContentType.objects.get_for_model(obj)
        
        obj_perms = set()
        obj_perms.update(self._get_generic_obj_permissions(user_obj, obj, ct=ct))
        
        if not user_obj.is_anonymous():
            # get any user user-specific permissions
            perms = Permission.objects.filter(rowlevel_user__user=user_obj,
                                              rowlevel_user__object_ct=ct,
                                              rowlevel_user__object_id=obj.id).values_list('content_type__app_label', 'codename').order_by()
            obj_perms.update(perms)

        return obj_perms

    def has_perm(self, user_obj, perm, obj=None):
        return perm in self.get_all_permissions(user_obj, obj=obj)
        
    def objects_with_perm(self, user_obj, perm, ModelType):
        """
        select identifiers of objects the type specified that the 
        user specified has the permission 'perm' set for.
        """
        ps = perm.index('.')
        app_label = perm[0:ps]
        codename = perm[ps+1:]
        
        perm = Permission.objects.get(content_type__app_label=app_label, codename=codename)
        ct = ContentType.objects.get_for_model(ModelType)

        obj_ids = set()

        generic_roles = [ANONYMOUS_USERS]
        if not user_obj.is_anonymous():
            generic_roles.append(AUTHENTICATED_USERS)
            obj_ids.update([x[0] for x in UserRowLevelPermission.objects.filter(user=user_obj,
                                                                                permission=perm,
                                                                                object_ct=ct).values_list('object_id').all()])
        for role in generic_roles: 
            obj_ids.update([x[0] for x in GenericRowLevelPermission.objects.filter(subject=role,
                                                                                   permission=perm,
                                                                                   object_ct=ct).values_list('object_id').all()])
        
        return obj_ids