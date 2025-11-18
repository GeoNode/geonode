import logging

from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.contrib.postgres.search import SearchVectorField

from geonode.base.models import ResourceBase

logger = logging.getLogger(__name__)


class ResourceIndex(models.Model):
    """
    A searchable index
    """

    resource = models.ForeignKey(ResourceBase, on_delete=models.CASCADE, null=False)
    lang = models.CharField(max_length=16, null=True, blank=False)
    name = models.CharField(max_length=64, null=False, blank=False)
    vector = SearchVectorField(null=False, blank=False)

    def __str__(self):
        return f"{self.lang}|{self.name}"

    class Meta:
        ordering = (
            "resource",
            "name",
            "lang",
        )
        unique_together = (("resource", "lang", "name"),)

        indexes = [
            GinIndex(
                fields=[
                    "vector",
                ]
            )
        ]
