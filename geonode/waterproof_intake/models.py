"""Models for the ``WaterProof Intake`` app."""

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

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

    id_region = models.CharField(
        max_length=24,
        verbose_name=_('Id Region'),
    )

    id_city = models.CharField(
        max_length=24,
        verbose_name=_('Id City'),
    )

    
