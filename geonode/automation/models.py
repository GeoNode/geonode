from django.db import models
from datetime import datetime
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices
from geonode.base.models import ResourceBase
from geonode.cephgeo.models import DataClassification, LidarCoverageBlock
from django_enumfield import enum
# Create your models here.


class AutomationJob(models.Model):
    """This class saves a worker job for metadata automation processes.

    Attributes:
        DATATYPE_CHOICES (tuple): Input data type to be processed.
        PROCESSOR_CHOICES (tuple): Component processor of input data based on
            UP TCAGP Phil-LiDAR Program components.
        STATUS_CHOICES (tuple): Status of jobs in Automation model.
        OS_CHOICES (tuple): Operating system options wherein data will be processed
        datatype (str): The datatype of input. Limited to DATATYPE_CHOICES.
        input_dir (str): Directory containing input data. Path folder is traversed
            in processing environment's server mount path.
        output_dir (str): Directory to contain output data. Path folder must be in
            processing environment's
        processor (str): The processor of input data. Limited to PROCESSOR_CHOICES.
        date_submitted (date): Date and time when an automation process\/job is submitted.
        status (str): Status of jobs. Limited to STATUS_CHOICES. The status define
            where the worker is in the Automation workflow. The following are the
            list of STATUS_CHOICES and definitions:

            #. pending_process (Pending Job): The task is not yet fetched by the
                database watcher from processing environment.
            #. done_process (Processing Job): Task is already received by Salad,
                processing the data begins. For LAZ/Orthophoto data, renaming and
                creation of output folder is done here. It is named \'Processing Job\'
                in case the processing environment goes down, resumption of
                processing starts from the top and discards previous output.
                This is done to preserve data integrity.
            #. pending_ceph (Uploading in Ceph):  Processing of data is done and
                is ready for upload in Ceph.
            #. done_ceph (Uploaded in Ceph): Processed data are ready to be uploaded
                to LiPAD. This trasnfers the metadata to LiPAD database.
            #. done (Uploaded in LiPAD): Metadata is uploaded in LiPAD.
        status_timestamp (date): Date and time of changing a job\'s status.
        target_os (str): Processing environment receiver's operating system. Limited
            to OS_CHOICES.
        log (str): Stores logs per transaction between processing. Includes renaming,
            processing, tiling, transfer logs.

    """

    DATATYPE_CHOICES = Choices(
        ('LAZ', _('LAZ')),
        ('Ortho', _('ORTHO')),
        ('DTM', _('DTM')),
        ('DSM', _('DSM')),
        ('Others', _('Others'))
    )

    PROCESSOR_CHOICES = Choices(
        ('DRM', _('DREAM')),
        ('PL1', _('Phil-LiDAR 1')),
        ('PL2', _('Phil-LiDAR 2')),
    )

    STATUS_CHOICES = Choices(
        ('pending_process', _('Pending Job')),
        ('done_process', _('Processed Job')),
        ('done_ceph', _('Uploaded in Ceph')),
        ('done', _('Uploaded in LiPAD')),

        # ('done_process', _('Processing Job')),
        # ('pending_ceph', _('Uploading in Ceph')),
        # (-1, 'error', _('Error')),
    )

    OS_CHOICES = Choices(
        ('linux', _('Process in Linux')),
        ('windows', _('Process in Windows')),
    )

    datatype = models.CharField(
        choices=DATATYPE_CHOICES,
        max_length=10,
        help_text=_('Datatype of input'),
    )

    input_dir = models.TextField(
        _('Input Directory'),
        blank=False,
        null=False,
        help_text=_('Full path of directory location in server')
    )

    output_dir = models.TextField(
        _('Output Directory'),
        blank=False,
        null=False,
        help_text=_('Folder location in server')
    )

    processor = models.CharField(
        _('Data Processor'),
        choices=PROCESSOR_CHOICES,
        max_length=10,
    )

    date_submitted = models.DateTimeField(
        default=datetime.now,
        blank=False,
        null=False,
        help_text=_('The date when the job was submitted in LiPAD')
    )

    status = models.CharField(
        _('Job status'),
        choices=STATUS_CHOICES,
        default=STATUS_CHOICES.pending_process,
        max_length=20
    )

    status_timestamp = models.DateTimeField(
        blank=True,
        null=True,
        help_text=_('The date when the status was updated'),
        default=datetime.now()
    )

    target_os = models.CharField(
        _('OS to Process Job'),
        choices=OS_CHOICES,
        default=OS_CHOICES.linux,
        max_length=20
    )

    data_processing_log = models.TextField(null=False, blank=True)
    ceph_upload_log = models.TextField(null=False, blank=True)
    database_upload_log = models.TextField(null=False, blank=True)

    def __unicode__(self):
        return "{0} {1} {2}". \
            format(self.datatype, self.date_submitted, self.status)


class CephDataObjectResourceBase(ResourceBase):
    """Explicitly inherits ResourceBase class.

    Object storage model for each `Ceph object storage` data entry. Each data input is
    divided into 1km by 1km. This data division is called `tile`.

    Attributes:
        size_in_bytes (int): Data entry size in bytes represented as intergers.
            Data entries are also called `Ceph objects`.
        file_hash (str): Hash output of source input file in Ceph object storage.
            This is a result of `Ceph`\'s hashing algorithm.
        name (str): String identifier of a Ceph object\'s source file. A data object
            name is the source input filename.
        last_modified (date): Records data of ceph object recent modification. This
            could be create, delete, updating data.
        content_type (str): Type representation of input spatial data. These are:
            - `image/tiff` for Digital Elevation Model and Orthophoto
            - `None` for LAZ files
        data_class (enum): Data classification of input data. These are:
            - LAZ
            - Orthophoto
            - Digital Elevation Model
                -  Digital Terrain Model
                - Digital Surface Model
        grid_ref (str): Grid reference or spatial coordinates of a data tile.
            Represented in easting and northing coordinate format.
        block_uid (:obj:`lidarcoverageblock`): Foreign key to `LidarCoverageBlock`
            model. Defines which LiDAR block the input data is part of.
            - In the case of LAZ and Orthophoto datatypes, mapping to a lidar coverage
                block is one-to-one.
            - For DEM, mapping to lidar coverage block is many-to-many.
    """
    size_in_bytes = models.IntegerField()
    file_hash = models.CharField(max_length=40)
    name = models.CharField(max_length=100)
    last_modified = models.DateTimeField()
    content_type = models.CharField(max_length=20)
    #geo_type        = models.CharField(max_length=20)
    data_class = enum.EnumField(
        DataClassification, default=DataClassification.UNKNOWN)
    grid_ref = models.CharField(max_length=10)
    block_uid = models.ForeignKey(LidarCoverageBlock, null=True, blank=True)

    def uid(self):
        """int: Returns unique identifier of corresponding lidar coverage block."""
        return self.block_uid.uid

    def block_name(self):
        """str: Returns block name of corresponding lidar coverage block."""
        return self.block_uid.block_name

    def __unicode__(self):
        """name, data_class: Returns file name and data class of CephDataObjectResourceBase
            object being queried."""
        return "{0}:{1}".format(self.name, DataClassification.labels[self.data_class])
