from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.conf import settings
from django.utils.translation import ugettext as _

from CommonField import CommonField


class Visitor(CommonField):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    page_name = models.CharField(_('Page Name'), max_length=250, null=True, blank=True, help_text='Page Name')

    def __str__(self):
        return self.user.username
