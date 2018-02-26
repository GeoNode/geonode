from  django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from .CommonField import CommonField


class LoadActivity(CommonField):
    content_type = models.ForeignKey(
        ContentType
        )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

