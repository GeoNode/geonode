from django.db import models
from django.conf import settings
from django.db.models import signals
from datetime import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver

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
    layer_purpose = models.CharField(
        verbose_name='Purpose of the Layer',
        max_length=20,
        blank=True,
        null=True,
        default=''
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

    @classmethod
    def get_exposure_layers(cls):
        """
        """
        pass


def get_metadata_url(layer):
    """Obtain the url of xml file of a layer.

    :param layer: A Layer object
    :type layer: Layer

    :returns: A url to the metadata file
    :rtype: str
    """
    xml_files = layer.upload_session.layerfile_set.filter(name='xml')
    xml_file_object = xml_files[len(xml_files) - 1] # get the latest index
    xml_file_url = xml_file_object.file.url

    return xml_file_url


@receiver(post_save, sender=Layer)
def create_metadata_object(sender, instance, created, **kwargs):
    metadata = Metadata()
    metadata.layer = instance
    metadata.layer_purpose = instance.layer_purpose()

    metadata.save()
