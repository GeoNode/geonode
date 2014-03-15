# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import signals
from geonode.base.models import ResourceBase, resourcebase_post_save, resourcebase_post_delete
from geonode.security.enumerations import AUTHENTICATED_USERS, ANONYMOUS_USERS

class Analysis(ResourceBase):
    last_modified = models.DateTimeField(auto_now_add=True)
    # The last time the map was modified.

    popular_count = models.IntegerField(default=0)

    share_count = models.IntegerField(default=0)

    data = models.TextField()

    LEVEL_READ  = 'analysis_readonly'
    LEVEL_WRITE = 'analysis_readwrite'
    LEVEL_ADMIN = 'analysis_admin'

    class Meta:
        # custom permissions,
        # change and delete are standard in django
        permissions = (('view_analysis', 'Can view'),
                       ('change_analysis_permissions', "Can change permissions"), )


    def set_default_permissions(self):
        self.set_gen_level(ANONYMOUS_USERS, self.LEVEL_READ)
        self.set_gen_level(AUTHENTICATED_USERS, self.LEVEL_READ)

        # remove specific user permissions
        current_perms =  self.get_all_level_info()
        for username in current_perms['users'].keys():
            user = User.objects.get(username=username)
            self.set_user_level(user, self.LEVEL_NONE)

        # assign owner admin privs
        if self.owner:
            self.set_user_level(self.owner, self.LEVEL_ADMIN)

    def class_name(self):
        return 'Analysis'

    def __unicode__(self):
        return self.title

def pre_save_analysis(instance, sender, **kwargs):
    pass

def pre_delete_analysis(instance, sender, **kwargs):
    pass

signals.pre_save.connect(pre_save_analysis, sender=Analysis)
signals.pre_delete.connect(pre_delete_analysis, sender=Analysis)
signals.post_save.connect(resourcebase_post_save, sender=Analysis)
signals.post_delete.connect(resourcebase_post_delete, sender=Analysis)
