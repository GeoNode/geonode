from django.utils.translation import ugettext as _
from  django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from .CommonField import CommonField
from geonode.analytics.enum import NonGISActivityTypeEnum

class LoadActivity(CommonField):
    content_type = models.ForeignKey(
        ContentType
        )
    activity_type = models.CharField(_('Activity Type'),
                                     choices=NonGISActivityTypeEnum.CHOICES,
                                     max_length=10,
                                     help_text=_('Activity Type'))
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

