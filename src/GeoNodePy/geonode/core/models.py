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
    ANONYMOUS_USERS: _("Anonymous Users"),
    AUTHENTICATED_USERS: _("Authenticated Users")
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