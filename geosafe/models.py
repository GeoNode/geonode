from django.db import models
from django.conf import settings
from datetime import datetime

from geonode.layers.models import Layer


# Create your models here.
class Metadata(models.Model):
    """Represent metadata for a layer."""
    layer = models.OneToOneField(Layer, primary_key=True)
    metadata_file = models.FileField(
        verbose_name='Metadata file',
        help_text='Metadata file for a layer..',
        upload_to='metadata',
        max_length=100
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        default=None,
        null=True,
        blank=True
    )
    date_created = models.DateTimeField(
        auto_now=True,
        default=datetime.utcnow,
        null=True,
        blank=True
    )
