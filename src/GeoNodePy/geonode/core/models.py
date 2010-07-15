from django.contrib.auth import authenticate, get_backends as get_auth_backends
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey
from django.db import models
from django.utils.translation import ugettext_lazy as _


class UserRowLevelPermission(models.Model):
    """
    represents the assignment of a Permission to a User in 
    the context of a particular object. 
    """

    user = models.ForeignKey(User, related_name="obj_permissions")

    object_ct = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey('object_ct', 'object_id')

    permission = models.ForeignKey(Permission, related_name="rowlevel_user")

    def __unicode__(self):
        return u"%s | %s -> %s" % (
            unicode(self.object),
            unicode(self.user), 
            unicode(self.permission))

    class Meta:
        unique_together = (('user', 'object_ct', 'object_id', 'permission'), ) 

# implicitly defined 'generic' groups of users 
ANONYMOUS_USERS = 'anonymous'
AUTHENTICATED_USERS = 'authenticated'
GENERIC_GROUP_NAMES = {
    ANONYMOUS_USERS: _('Anonymous Users'),
    AUTHENTICATED_USERS: _('Registered Users')
}

class GenericRowLevelPermission(models.Model):
    """
    represents assignment of a permission to an arbitrary implicitly 
    defined group of users (groups without explicit database representation) 
    in the context of a specific object. eg 'all authenticated users' 
    'anonymous users', 'users <as defined by some other service>'
    """
    
    subject = models.CharField(max_length=100, choices=sorted(GENERIC_GROUP_NAMES.items()))

    object_ct = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey('object_ct', 'object_id')
    
    permission = models.ForeignKey(Permission, related_name="rowlevel_generic")

    def __unicode__(self):
        return u"%s | %s -> %s" % (
            unicode(self.object),
            unicode(GENERIC_GROUP_NAMES[self.subject]), 
            unicode(self.permission))

    class Meta:
        unique_together = (('subject', 'object_ct', 'object_id', 'permission'), )
        
def PermissionLevelError(Exception):
    pass

class PermissionLevelMixin(object):
    """
    Mixin for adding "Permission Level" methods 
    to a model class.  the class must define list 
    of permission levels LEVEL_PERM defining which
    model Permissions are granted at each level, eg: 
    
    [
    {'widget.view': True,
     'widget.edit': False,
     'widget.delete': False
    },
    {'widget.view': True,
     'widget.edit': True,
     'widget.delete': False
    },
    {'widget.view': True,
     'widget.edit': True,
     'widget.delete': True
    } 
    ]
    """

    def get_user_permissions(self, user):
        """
        returns the names of all Permissions the given user 
        has for this object, including those inherited 
        from generic roles.
        """
        for bck in get_auth_backends():
            if bck.supports_object_permissions:
                return bck.get_all_permissions(user, obj=self)


    def get_user_level(self, user):
        """
        get the permission level (if any) specifically assigned to the given user.
        this may return -1 to indicate an unidentifiable or custom grouping of permissions
        has been set.
        """
        def has_perm(perm):
            return user.has_perm(perm, obj=self)
        return _identify_permission_level(has_perm, self.LEVEL_PERM)

    def set_user_level(self, user, level):
        """
        grant exactly the set of permissions in the level specified to 
        the specific user listed. 
        """

        if level < 0 or level >= len(self.LEVEL_PERM):  
            raise PermissionLevelError("Invalid Permission Level (%s)" % level)

        perms = self.LEVEL_PERM[level]
        perms = [x for (x, k) in perms.items() if k == True]

        for bck in get_auth_backends():
            if hasattr(bck, 'set_all_generic_obj_perms'):
                bck.set_all_user_obj_perms(user, self, perms) 

    def get_gen_level(self, gen_role):
        """
        get the permission level (if any) specifically assigned to the given generic
        group of users.  This may return -1 to indicate an unidentifiable or custom
        grouping of permissions has been set.
        """

        for bck in get_auth_backends():
            if hasattr(bck, 'get_generic_obj_perms'):
                perms = bck.get_generic_obj_perms(gen_role, obj=self)

                def has_perm(perm):
                    return perm in perms
                return _identify_permission_level(has_perm, self.LEVEL_PERM)
        return -1

    def set_gen_level(self, gen_role, level):
        """
        grant exactly the set of permissions in the level specified to 
        the specific user listed. 
        """

        if level < 0 or level >= len(self.LEVEL_PERM):  
            raise PermissionLevelError("Invalid Permission Level (%s)" % level)

        perms = self.LEVEL_PERM[level]
        perms = [x for (x, k) in perms.items() if k == True]

        for bck in get_auth_backends():
            if hasattr(bck, 'set_all_generic_obj_perms'):
                bck.set_all_generic_obj_perms(gen_role, self, perms) 

    def get_all_level_info(self):
        """
        returns a mapping indicating the permission levels
        of users, anonymous users any authenticated users that
        have specific permissions assigned to them.

        The mapping may contain -1 as a level to indicate an 
        unknown / custom permission setting.

        the mapping looks like: 
        {
            'anonymous': 0, 
            'authenticated': 1,
            'users': {
                <username>: 2
                ...
            }
        } 
        """
        # get all user-specific permissions
        user_levels = {}
        for bck in get_auth_backends():
            if hasattr(bck, 'get_all_user_object_perms'):
                for username, perms in bck.get_all_user_object_perms(self).items():
                    user_levels[username] = _identify_permission_level(perms.__contains__, self.LEVEL_PERM)

        levels = {}
        # XXX could grab any custom ones too...
        levels[ANONYMOUS_USERS] = self.get_gen_level(ANONYMOUS_USERS)
        levels[AUTHENTICATED_USERS] = self.get_gen_level(AUTHENTICATED_USERS)
        levels['users'] = user_levels

        return levels

def _identify_permission_level(has_perm, levels):
   for i, level in enumerate(levels):
       has_all = True
       for (perm, state) in level.items():
           if has_perm(perm) != state:
               has_all = False
               break
       if has_all:
           return i
   return -1
