from django.db import models
from geonode.layers.models import Layer
from django.conf import settings
from datetime import datetime
import json
from geonode.people.models import Profile
from geonode.groups.models import GroupProfile
from django.utils.translation import ugettext_lazy as _
from taggit.managers import TaggableManager

try:
    from django.conf import settings
    User = settings.AUTH_USER_MODEL
except ImportError:
    from django.contrib.auth.models import User

from django_enumfield import enum


class DataClassification(enum.Enum):
    UNKNOWN = 0
    LAZ = 1
#    DEM = 2
    DTM = 3
    DSM = 4
    ORTHOPHOTO = 5

    labels = {
        UNKNOWN: "Unknown Type",
        LAZ: "LAZ",
        #        DEM         : "DEM TIF",
        DSM: "DSM TIF",
        DTM: "DTM TIF",
        ORTHOPHOTO: "Orthophoto", }

    gs_feature_labels = {
        UNKNOWN: "UNSUPPORTED",
        LAZ: "LAZ",
        #        DEM         : "UNSUPPORTED",
        DSM: "DSM",
        DTM: "DTM",
        ORTHOPHOTO: "ORTHO", }

    filename_suffixes = {
        ".laz": LAZ,
        #        "_dem.tif"         : DEM,
        "_dsm.tif": DSM,
        "_dtm.tif": DTM,
        "_ortho.tif": ORTHOPHOTO, }


class FTPStatus(enum.Enum):
    DONE = 0
    PENDING = 1
    ERROR = 2
    DUPLICATE = 3
    FORWARDED = 4

    labels = {
        DONE: 'Done',
        PENDING: 'Pending',
        ERROR:   'Error',
        DUPLICATE: 'Duplicate',
        FORWARDED: 'Forwarded'}


class TileDataClass(models.Model):
    short_name = models.CharField(max_length=15)
    full_name = models.CharField(max_length=50)
    description = models.CharField(max_length=300)

    def __unicode__(self):
        return "{0}:{1}".format(self.short_name, self.full_name)


class FTPRequest(models.Model):
    name = models.CharField(max_length=50)
    date_time = models.DateTimeField(default=datetime.now)
    user = models.ForeignKey(User, null=False, blank=False)
    status = enum.EnumField(FTPStatus, default=FTPStatus.PENDING)
    size_in_bytes = models.BigIntegerField()
    num_tiles = models.IntegerField()

    def __unicode__(self):
        return "{0}:{1}".format(self.name, self.user.username)


class EULA(models.Model):
    user = models.ForeignKey(User, null=False, blank=False)
    document = models.FileField(upload_to=settings.MEDIA_ROOT)


class UserJurisdiction(models.Model):
    user = models.ForeignKey(Profile, null=False, blank=False)
    jurisdiction_shapefile = models.ForeignKey(Layer, null=True, blank=True)

    def get_shapefile_typename(self):
        return self.jurisdiction_shapefile.service_typename

    def get_user_name(self):
        return self.user.username


class UserTiles(models.Model):
    user = models.ForeignKey(Profile, null=False, blank=False, unique=True)
    gridref_list = models.TextField(null=False, blank=False)

    @property
    def num_tiles(self):
        return self.gridref_list.count(',') + 1


class MissionGridRef(models.Model):
    fieldID = models.IntegerField()
    grid_ref = models.CharField(max_length=20)

    def __unicode__(self):
        return "{0}:{1}".format(self.grid_ref, self.fieldID)


class SucToLayer(models.Model):
    suc = models.CharField(max_length=20)
    block_name = models.CharField(max_length=40)

    def __unicode__(self):
        return "{0}:{1}".format(self.suc, self.block_name)


class RIDF(models.Model):
    prov_code = models.CharField(max_length=11)
    prov_name = models.CharField(max_length=50)
    muni_code = models.CharField(max_length=11)
    muni_name = models.CharField(max_length=50)
    iscity = models.BooleanField(default=False)
    _5yr = models.DecimalField(
        max_digits=7, decimal_places=3, null=True, default=0)
    _25yr = models.DecimalField(
        max_digits=7, decimal_places=3, null=True, default=0)
    _100yr = models.DecimalField(
        max_digits=7, decimal_places=3, null=True, default=0)
    rbs_raw = models.CharField(max_length=100, null=True, blank=True)
    riverbasins = TaggableManager(
        _('riverbasins'), blank=True, help_text='List of riverbasins')

    # def keyword_list(self):
    #     """
    #     Returns a list of the Area's riverbasins.
    #     """
    #     return [kw.name for kw in self.riverbasins.all()]

    def __unicode__(self):
        return "{0}:{1}".format(self.prov_name, self.muni_name)


class LidarCoverageBlock(models.Model):
    """
        Help text for attributes
    """
    uid_ht = _('(DAD) Unique ID of each Lidar Coverage Block')
    block_name_ht = _('(DPPC) Unique ID of each Lidar Coverage Block')
    adjusted_l_ht = _('(DPPC) If LAZ data is adjusted')
    sensor_ht = _('(DAC) Sensor equipment used for this block')
    processor_ht = _('(DPPC) Processed as DREAM or Phil-LiDAR 1 data')
    flight_num_ht = _('(DAC) Flight number/s for this block')
    mission_na_ht = _('(DAC) Mission name/s for this block')
    date_flown_ht = _('(DAC) Date the data was acquired')
    x_shift_m_ht = _('(DPPC) X-Axis shifting value')
    y_shift_m_ht = _('(DPPC) Y-Axis shifting value')
    z_shift_m_ht = _('(DPPC) Z-Axis shifting value')
    height_dif_ht = _('(DPPC) Height Difference')
    rmse_val_m_ht = _('(DPPC) Root Mean Square Error values from DPPC')
    cal_ref_pt_ht = _('(DAC) list of calibration reference points per block')
    val_ref_pt_ht = _('(DVC) list of validation reference points per block')
    floodplain_ht = _('(DPPC) Floodplain associated with this block')
    pl1_suc_ht = _('(DPPC) Phil-LiDAR 1 SUC assigned to this block')
    pl2_suc_ht = _('(DPPC) Phil-LiDAR 2 SUC assigned to this block')

    uid = models.IntegerField(primary_key=True, help_text=uid_ht)
    block_name = models.CharField(
        max_length=255, unique=True, help_text=block_name_ht)
    adjusted_l = models.TextField(blank=True, help_text=adjusted_l_ht)
    sensor = models.TextField(blank=True, help_text=sensor_ht)
    processor = models.TextField(blank=True, help_text=processor_ht)
    flight_num = models.TextField(blank=True, help_text=flight_num_ht)
    mission_na = models.TextField(blank=True, help_text=mission_na_ht)
    date_flown = models.DateField(
        blank=True, null=True, help_text=date_flown_ht)
    x_shift_m = models.TextField(blank=True, help_text=x_shift_m_ht)
    y_shift_m = models.TextField(blank=True, help_text=y_shift_m_ht)
    z_shift_m = models.TextField(blank=True, help_text=z_shift_m_ht)
    height_dif = models.TextField(blank=True, help_text=height_dif_ht)
    rmse_val_m = models.TextField(blank=True, help_text=rmse_val_m_ht)
    cal_ref_pt = models.TextField(blank=True, help_text=cal_ref_pt_ht)
    val_ref_pt = models.TextField(blank=True, help_text=val_ref_pt_ht)
    floodplain = models.TextField(blank=True, help_text=floodplain_ht)
    pl1_suc = models.TextField(blank=True, help_text=pl1_suc_ht)
    pl2_suc = models.TextField(blank=True, help_text=pl2_suc_ht)

    def __unicode__(self):
        return "{0}:{1}".format(self.uid, self.block_name)

    class Meta:
        verbose_name_plural = 'Lidar Coverage Blocks'


class CephDataObject(models.Model):
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

    # @property
    # def block_uid(self):
    #     return self.block_uid.uid

    # def block_name(self):
    #     return self.block_uid.block_name

    def __unicode__(self):
        return "{0}:{1}".format(self.name, DataClassification.labels[self.data_class])


class FTPRequestToObjectIndex(models.Model):
    from geonode.automation.models import CephDataObjectResourceBase
    # FTPRequest
    ftprequest = models.ForeignKey(FTPRequest, null=False, blank=False)
    # CephObject
    cephobject = models.ForeignKey(CephDataObjectResourceBase, null=False, blank=False)
    # cephobject = models.ForeignKey(CephDataObject, null=False, blank=False)
