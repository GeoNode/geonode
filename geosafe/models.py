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
        help_text='Metadata file for a layer.',
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


class Analysis(models.Model):
    """Represent GeoSAFE analysis"""
    HAZARD_EXPOSURE_CURRENT_VIEW_CODE = 1
    HAZARD_EXPOSURE_CODE = 2
    HAZARD_EXPOSURE_BBOX_CODE = 3

    HAZARD_EXPOSURE_CURRENT_VIEW_TEXT = (
        'Use intersection of hazard, exposure, and current view extent')
    HAZARD_EXPOSURE_TEXT = 'Use intersection of hazard and exposure'
    HAZARD_EXPOSURE_BBOX_TEXT = (
        'Use intersection of hazard, exposure, and bounding box')

    EXTENT_CHOICES = (
        (HAZARD_EXPOSURE_CURRENT_VIEW_CODE, HAZARD_EXPOSURE_CURRENT_VIEW_TEXT),
        (HAZARD_EXPOSURE_CODE, HAZARD_EXPOSURE_TEXT),
        # Disable for now
        # (HAZARD_EXPOSURE_BBOX_CODE, HAZARD_EXPOSURE_BBOX_TEXT),
    )

    exposure_layer = models.ForeignKey(
        Layer,
        verbose_name='Exposure Layer',
        help_text='Exposure layer for analysis.',
        blank=False,
        null=False,
        related_name='exposure_layer'
    )
    hazard_layer = models.ForeignKey(
        Layer,
        verbose_name='Hazard Layer',
        help_text='Hazard layer for analysis.',
        blank=False,
        null=False,
        related_name='hazard_layer'
    )
    aggregation_layer = models.ForeignKey(
        Layer,
        verbose_name='Aggregation Layer',
        help_text='Aggregation layer for analysis.',
        blank=True,
        null=True,
        related_name='aggregation_layer'
    )
    impact_function_id = models.CharField(
        max_length=100,
        verbose_name='ID of Impact Function',
        help_text='The ID of Impact Function used in the analysis.',
        blank=False,
        null=False
    )
    extent_option = models.IntegerField(
        choices=EXTENT_CHOICES,
        default=HAZARD_EXPOSURE_CURRENT_VIEW_CODE,
        verbose_name='Analysis extent',
        help_text='Extent option for analysis.'
    )
