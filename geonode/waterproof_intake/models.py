"""Models for the ``WaterProof Intake`` app."""

from django.conf import settings
from django.db import models
from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _
from geonode.waterproof_nbs_ca.models import Countries


class City(models.Model):
    country = models.ForeignKey(Countries, on_delete=models.CASCADE)

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
    )

    def __str__(self):
        return "%s" % self.name


class Intake(models.Model):
    """
    Model to Waterproof Intake.

    :name: Intake Name.
    :descripcion: Intake Description.

    """

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
    )

    description = models.CharField(
        max_length=1024,
        verbose_name=_('Description'),
    )

    area = models.MultiPolygonField(verbose_name='geo',srid = 4326, null=True, blank=True)
    
    city = models.ForeignKey(Countries, on_delete=models.CASCADE)

    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )


class UserCosts(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
    )

    value = models.DecimalField(
        decimal_places=4,
        max_digits=14,
        verbose_name=_('Value')
    )

class CategoryCosts(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
    )

    description=models.CharField(
        max_length=100,
        verbose_name=_('Name'),
    )

class SystemCosts(models.Model):

    name = models.CharField(
        max_length=100,
        verbose_name=_('Name'),
    )

    value = models.DecimalField(
        decimal_places=4,
        max_digits=14,
        verbose_name=_('Extraction value')
    )

   
class ElementSystem(models.Model):
    origin = models.IntegerField(
        default=1980,
        verbose_name=_('Year'),
    )

    destination = models.IntegerField(
        default=1980,
        verbose_name=_('Year'),
    )

    user_cost=models.ManyToManyField(
        UserCosts,
    )

    system_cost=models.ManyToManyField(
        SystemCosts,
    )


class ExternalInputs(models.Model):
    year = models.IntegerField(
        default=1980,
        verbose_name=_('Year'),
    )

    water_volume = models.DecimalField(
        decimal_places=4,
        max_digits=14,
        verbose_name=_('Water_volume')
    )

    sediment = models.DecimalField(
        decimal_places=4,
        max_digits=14,
        verbose_name=_('Extraction value')
    )

    nitrogen = models.DecimalField(
        decimal_places=4,
        max_digits=14,
        verbose_name=_('Extraction value')
    )

    phosphorus = models.DecimalField(
        decimal_places=4,
        max_digits=14,
        verbose_name=_('Extraction value')
    )

    intake = models.ForeignKey(Intake, on_delete=models.CASCADE)


class DemandParameters(models.Model):

    initial_year = models.IntegerField(
        verbose_name=_('Year'),
    )

    ending_year = models.IntegerField(
        verbose_name=_('Year'),
    )

    interpolation_type = models.IntegerField(
        verbose_name=_('Year'),
    )

    initial_extraction = models.DecimalField(
        decimal_places=4,
        max_digits=14,
        verbose_name=_('Extraction value')
    )

    ending_extraction = models.DecimalField(
        decimal_places=4,
        max_digits=14,
        verbose_name=_('Extraction value')
    )

    is_manual = models.BooleanField(verbose_name=_('Manual'), default=False)

    intake = models.ForeignKey(Intake, on_delete=models.CASCADE)


class WaterExtraction(models.Model):
    year = models.IntegerField(
        default=1980,
        verbose_name=_('Year'),
    )

    value = models.DecimalField(
        decimal_places=4,
        max_digits=14,
        verbose_name=_('Extraction value')
    )

    demand = models.ForeignKey(DemandParameters, on_delete=models.CASCADE)
