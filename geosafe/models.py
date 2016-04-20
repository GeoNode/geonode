from __future__ import absolute_import

import tempfile
import urlparse

from django.conf import settings
from django.core.files.base import File
from django.core.urlresolvers import reverse
from django.db import models
from celery.result import AsyncResult

from geonode.layers.models import Layer
from geonode.people.models import Profile

# geosafe
import os
from xml.etree import ElementTree

# geosafe
# list of tags to get to the InaSAFE keywords.
# this is stored in a list so it can be easily used in a for loop

ISO_METADATA_KEYWORD_NESTING = [
    '{http://www.isotc211.org/2005/gmd}identificationInfo',
    '{http://www.isotc211.org/2005/gmd}MD_DataIdentification',
    '{http://www.isotc211.org/2005/gmd}supplementalInformation',
    'inasafe_keywords']

# flat xpath for the keyword container tag
ISO_METADATA_KEYWORD_TAG = '/'.join(ISO_METADATA_KEYWORD_NESTING)


class GeoSAFEException(BaseException):
    pass


# Create your models here.
class Metadata(models.Model):
    """Represent metadata for a layer."""
    layer = models.OneToOneField(Layer, primary_key=True,
                                 related_name='metadata')
    layer_purpose = models.CharField(
        verbose_name='Purpose of the Layer',
        max_length=20,
        blank=True,
        null=True,
        default=''
    )
    category = models.CharField(
        verbose_name='The category of layer purpose that describes a kind of'
                     'hazard or exposure this layer is',
        max_length=30,
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

    class Meta:
        verbose_name_plural = 'Analyses'

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
        default=HAZARD_EXPOSURE_CODE,
        verbose_name='Analysis extent',
        help_text='Extent option for analysis.'
    )

    impact_layer = models.ForeignKey(
        Layer,
        verbose_name='Impact Layer',
        help_text='Impact layer from this analysis.',
        blank=True,
        null=True,
        related_name='impact_layer'
    )

    task_id = models.CharField(
        max_length=40,
        verbose_name='Task UUID',
        help_text='Task UUID that runs analysis',
        blank=True,
        null=True
    )

    keep = models.BooleanField(
        verbose_name='Keep impact result',
        help_text='True if the impact will be kept',
        blank=True,
        default=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Author',
        help_text='The author of the analysis',
        blank=True,
        null=True
    )

    report_map = models.FileField(
        verbose_name='Report Map',
        help_text='The map report of the analysis',
        blank=True,
        null=True,
        upload_to='analysis/report/'
    )

    report_table = models.FileField(
        verbose_name='Report Table',
        help_text='The table report of the analysis',
        blank=True,
        null=True,
        upload_to='analysis/report/'
    )

    def assign_report_map(self, filename):
        try:
            self.report_map.delete()
        except:
            pass
        self.report_map = File(open(filename))

    def assign_report_table(self, filename):
        try:
            self.report_table.delete()
        except:
            pass
        self.report_table = File(open(filename))

    def get_task_result(self):
        return AsyncResult(self.task_id)

    def get_label_class(self):
        result = self.get_task_result()
        if result.state == 'SUCCESS':
            return 'success'
        elif result.state == 'FAILURE':
            return 'danger'
        else:
            return 'info'

    def get_default_impact_title(self):
        layer_name = '%s on %s' % (
            self.hazard_layer.name,
            self.exposure_layer.name
        )
        return layer_name

    @classmethod
    def get_layer_url(cls, layer):
        layer_id = layer.id
        layer_url = reverse(
            'geosafe:layer-archive',
            kwargs={'layer_id': layer_id})
        layer_url = urlparse.urljoin(settings.GEONODE_BASE_URL, layer_url)
        return layer_url

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, run_analysis_flag=True):
        super(Analysis, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields)

    def delete(self, using=None):
        try:
            self.report_map.delete()
        except:
            pass

        try:
            self.report_table.delete()
        except:
            pass

        try:
            self.impact_layer.delete()
        except:
            pass
        super(Analysis, self).delete(using=using)


# needed to load signals
from geosafe import signals  # noqa
