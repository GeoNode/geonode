# -*- coding: utf-8 -*-
from django.db import models
from geonode.base.models import ResourceBase

class Analysis(ResourceBase):
  last_modified = models.DateTimeField(auto_now_add=True)  
  # The last time the map was modified.
  
  popular_count = models.IntegerField(default=0)
  
  share_count = models.IntegerField(default=0)
  
  def __unicode__(self):
    return self.title

