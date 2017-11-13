from django.db import models
from django_db_logger.models import StatusLog
from django.conf import settings

# Create your models here.


class ErrorLoggingAndReporting(StatusLog):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    custom_msg = models.TextField()

    def __str__(self):
        return self.user.username
