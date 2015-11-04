from django.db import models
from django.conf import settings
from django.db.models import signals
from datetime import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver
import tempfile

from geonode.layers.models import Layer
from geonode.people.models import Profile

# geosafe
import os
from xml.etree import ElementTree
from ast import literal_eval
from collections import OrderedDict
from geosafe.tasks.analysis import run_analysis_docker


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

    def get_metadata_file_path(self):
        """Obtain metadata (.xml) file path of the layer."""
        base_file, _ = self.layer.get_base_file()
        if not base_file:
            return ''
        base_file_path = base_file.file.path
        xml_file_path = base_file_path.split('.')[0] + '.xml'
        if not os.path.exists(xml_file_path):
            return ''
        return xml_file_path

    def inasafe_metadata(self):
        """Return dictionary of inasafe metadata."""
        xml_file_path = self.get_metadata_file_path()
        keywords = self.read_iso_metadata(xml_file_path)
        keywords = keywords['keywords']
        # remove empty line
        keywords = [x for x in keywords if x]
        keyword_dict = {}
        for item in keywords:
            if ':' not in item:
                key = item.strip()
                val = None
            else:
                # Get splitting point
                idx = item.find(':')

                # Take key as everything up to the first ':'
                key = item[:idx]

                # Take value as everything after the first ':'
                textval = item[idx + 1:].strip()
                try:
                    # Take care of python structures like
                    # booleans, None, lists, dicts etc
                    val = literal_eval(textval)
                except (ValueError, SyntaxError):
                    if 'OrderedDict(' == textval[:12]:
                        try:
                            val = OrderedDict(
                                literal_eval(textval[12:-1]))
                        except (ValueError, SyntaxError, TypeError):
                            val = textval
                    else:
                        val = textval

            # Add entry to dictionary
            keyword_dict[key] = val
        return keyword_dict

    def set_layer_purpose(self):
        """Obtain layer's purpose"""
        keywords = self.inasafe_metadata()
        self.layer_purpose = keywords.get('layer_purpose', '')

    @staticmethod
    def read_iso_metadata(keyword_filename):
        """Try to extract keywords from an xml file

        :param keyword_filename: Name of keywords file.
        :type keyword_filename: str

        :returns: metadata: a dictionary containing the metadata.
            the keywords element contains the content of the ISO_METADATA_KW_TAG
            as list so that it can be read line per line as if it was a file.

        :raises: ReadMetadataError, IOError
        """

        basename, _ = os.path.splitext(keyword_filename)
        xml_filename = basename + '.xml'

        # this raises a IOError if the file doesn't exist
        tree = ElementTree.parse(xml_filename)
        root = tree.getroot()

        keyword_element = root.find(ISO_METADATA_KEYWORD_TAG)
        # we have an xml file but it has no valid container
        if keyword_element is None:
            raise GeoSAFEException

        metadata = {'keywords': keyword_element.text.split('\n')}

        return metadata


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

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Author',
        help_text='The author of the analysis',
        blank=True,
        null=True
    )

    def generate_cli(self):
        """Generating CLI command to run analysis in InaSAFE headless.

        inasafe --hazard=HAZARD_FILE (--download --layers=LAYER_NAME [LAYER_NAME...] | --exposure=EXP_FILE)
            --impact-function=IF_ID --report-template=TEMPLATE --output-file=FILE [--extent=XMIN:YMIN:XMAX:YMAX]
        """
        hazard_file_path = self.hazard_layer.get_base_file()[0].file.path
        exposure_file_path = self.exposure_layer.get_base_file()[0].file.path
        # Save for later.
        # aggregation_file_path = self.aggregation_layer.get_base_file()[0].file.path

        arguments = ''
        arguments += '--hazard=' + hazard_file_path + ' '
        arguments += '--exposure=' + exposure_file_path + ' '
        arguments += '--impact-function=' + self.impact_function_id + ' '
        arguments += '--report-template= '  # later
        _, exposure_extension = os.path.splitext(exposure_file_path)
        if exposure_extension == '.shp':
            output_extension = '.shp'
        else:
            output_extension = '.tif'
        temp_file = os.path.join(
            tempfile._get_default_tempdir(),
            tempfile._get_candidate_names().next())+output_extension
        arguments += '--output-file=' + temp_file

        return arguments, temp_file, os.path.dirname(hazard_file_path), os.path.dirname(temp_file)

@receiver(post_save, sender=Layer)
def create_metadata_object(sender, instance, created, **kwargs):
    metadata = Metadata()
    metadata.layer = instance
    metadata.set_layer_purpose()

    metadata.save()


@receiver(post_save, sender=Analysis)
def run_analysis_post_save(sender, instance, created, **kwargs):
    """Call InaSAFE headless here"""
    arguments, output_file, layer_folder, output_folder = instance.generate_cli()
    run_analysis_docker.delay(arguments=arguments, output_file=output_file, layer_folder=layer_folder, output_folder=output_folder)
