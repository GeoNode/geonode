from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.conf import settings


class CommonField(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)    
    latitude = models.FloatField(_('Latitude'), null=True, blank=True, help_text='Latitude')
    longitude = models.FloatField(_('Longitude'), null=True, blank=True, help_text='Longitude')
    agent = models.CharField(_('User Agent'), max_length=250, null=True, blank=True, help_text='User Agent')
    ip = models.CharField(_('IP Address'), max_length=100, null=True, blank=True, help_text='IP Address')
    created_date = models.DateTimeField(_('Created Date'), auto_now_add=True, help_text='Created Date')
    last_modified = models.DateTimeField(_('Last Modified'), auto_now=True, help_text='Last Modified')

    @property
    def last_modified_date(self):
        'extracts the last_modified date from an entity'
        return self.last_modified.date()

    class Meta:
        abstract = True
