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
                all_perms = ['%s.%s' % p for p in self._get_all_obj_perms(user_obj, obj)]
                user_obj._obj_perm_cache[obj_key] = all_perms
                return all_perms
    
    def get_generic_obj_perms(self, generic_role, obj):
        if not hasattr(obj, '_gen_perm_cache'):
            # TODO: this cache should really be bounded.
            # repoze.lru perhaps?
            obj._gen_perm_cache = dict()
        try:
            key = generic_role
            return obj._gen_perm_cache[key]
        except KeyError: 
            perms = ['%s.%s' % p for p in self._get_generic_obj_perms([generic_role], obj)]
            obj._gen_perm_cache[key] = perms
            return perms

    def _cache_key_for_obj(self, obj):
        model = obj.__class__
        opts = model._meta
        while opts.proxy:
            model = opts.proxy_for_model
            opts = model._meta
        key = (opts.app_label, opts.object_name.lower(), obj.id)
        return key
    
        
    def _get_generic_obj_perms(self, generic_roles, obj, ct=None):
        perms = set()

        if ct is None:
            ct = ContentType.objects.get_for_model(obj)

        perms = Permission.objects.filter(rowlevel_generic__subject__in=generic_roles,
                                          rowlevel_generic__object_ct=ct,
                                          rowlevel_generic__object_id=obj.id).values_list('content_type__app_label', 'codename').order_by()
        return perms


    def _get_all_obj_perms(self, user_obj, obj, ct=None):
        """
        get all permissions for user in the context of ob (not cached)
        """
        if ct is None: 
            ct = ContentType.objects.get_for_model(obj)
        
        obj_perms = set()
        generic_roles = [ANONYMOUS_USERS]
        if not user_obj.is_anonymous():
            generic_roles.append(AUTHENTICATED_USERS)        
        obj_perms.update(self._get_generic_obj_perms(generic_roles, obj, ct=ct))
        
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
        
        if not isinstance(perm, Permission):
            perm = self._permission_for_name(perm)
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
        
    def _permission_for_name(self, perm):
        ps = perm.index('.')
        app_label = perm[0:ps]
        codename = perm[ps+1:]
        return Permission.objects.get(content_type__app_label=app_label, codename=codename)
        
    def _name_for_permission(self, perm):
        return '%s.%s' % (perm.content_type.app_label, perm.codename)

    def set_all_generic_obj_perms(self, generic_role, obj, perms):
        """Helper function to set the list of permissions for a generic role and object 
           to exactly some list"""
        # destroy all current GenericRowLevelPermissions
        
        ct = ContentType.objects.get_for_model(obj)
        GenericRowLevelPermission.objects.filter(subject=generic_role,
                                                 object_ct=ct,
                                                 object_id=obj.id).delete()
        for perm in perms:
            if not isinstance(perm, Permission):
                perm = self._permission_for_name(perm)
            GenericRowLevelPermission.objects.create(subject=generic_role, 
                                                     permission=perm,
                                                     object_ct=ct,
                                                     object_id=obj.id)
        
    def set_all_user_obj_perms(self, user_obj, obj, perms):
        """Helper function to set the list of permissions for a specific user and object 
           to exactly some list"""
        
        ct = ContentType.objects.get_for_model(obj)
        UserRowLevelPermission.objects.filter(user=user_obj,
                                              object_ct=ct,
                                              object_id=obj.id).delete()
        for perm in perms:
            if not isinstance(perm, Permission):
                perm = self._permission_for_name(perm)
            UserRowLevelPermission.objects.create(user=user_obj,
                                                  permission=perm,
                                                  object_ct=ct,
                                                  object_id=obj.id)

    def get_all_user_object_perms(self, obj):
        """
        helper, get all permissions set on a particular object organized by user.
        """
        perms = {}
        ct = ContentType.objects.get_for_model(obj)
        for perm in UserRowLevelPermission.objects.filter(object_id=obj.id, object_ct=ct).all():
            pname = self._name_for_permission(perm.permission)
            perms.setdefault(perm.user.username, set()).add(pname)
        return perms

