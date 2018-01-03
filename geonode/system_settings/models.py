from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from system_settings_enum import SystemSettingsEnum


class SystemSettings(models.Model):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    settings_code = models.CharField(_('Settings For'), max_length=250, choices=SystemSettingsEnum.SYSTEM_SETTINGS_CHOICES, help_text='Settings For', unique=True, null=False, blank=False)

    value = models.CharField(_('Value'), max_length=255, null=True, blank=True, help_text='Value')

    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Modified by'), related_name='system_settings_modified_by', help_text=_('Designates user who updates the record.'), )
    created_date = models.DateTimeField(_('Created Date'), auto_now_add=True, help_text='Created Date')
    last_modified = models.DateTimeField(_('Last Modified'), auto_now=True, help_text='Last Modified')

    def __str__(self):
        return self.settings_code


