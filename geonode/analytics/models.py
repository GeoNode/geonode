# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import signals
from geonode.base.models import ResourceBase, resourcebase_post_save, resourcebase_post_delete
from django.core.urlresolvers import reverse

class Analysis(ResourceBase):
    last_modified = models.DateTimeField(auto_now_add=True)
    # The last time the map was modified.

    popular_count = models.IntegerField(default=0)

    share_count = models.IntegerField(default=0)

    data = models.TextField()

    LEVEL_READ = 'analysis_readonly'
    LEVEL_WRITE = 'analysis_readwrite'
    LEVEL_ADMIN = 'analysis_admin'

    class Meta(object):
        # custom permissions,
        # change and delete are standard in django
        permissions = (('view_analysis', 'Can view'),
                       ('change_analysis_permissions', "Can change permissions"), )

    def get_absolute_url(self):
        return reverse('geonode.analytics.views.analysis_detail', None, [str(self.id)])

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
