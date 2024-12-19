import logging

from django.db import models

from geonode.base.models import ResourceBase


logger = logging.getLogger(__name__)

# class SparseFieldDecl(models.Model):
#     class Type(enum.Enum):
#         STRING = 'string'
#         INTEGER = 'integer'
#         FLOAT = 'float'
#         BOOL = 'bool'
#
#     FIELD_TYPES = []
#     name = models.CharField(max_length=64, null=False, blank=False, unique=True, primary_key=True)
#
#     type = models.CharField(choices=[(x.value,x.name) for x in Type], max_length=32, null=False, blank=False, unique=True, )
#     nullable = models.BooleanField(default=True, null=False)
#
#     eager = models.BooleanField(default=True, null=False)


class SparseField(models.Model):
    """
    Sparse field related to a ResourceBase
    """

    resource = models.ForeignKey(ResourceBase, on_delete=models.CASCADE, null=False)
    # name = models.ForeignKey(SparseFieldDecl, on_delete=models.PROTECT, null=False)
    name = models.CharField(max_length=64, null=False, blank=False)
    value = models.CharField(max_length=1024, null=True, blank=True)

    def __str__(self):
        return f"{self.name}={self.value}"

    @staticmethod
    def get_fields(resource: ResourceBase, names=None):
        qs = SparseField.objects.filter(resource=resource)
        if names:
            qs = qs.filter(name__in=names)

        return qs.all()

    class Meta:
        ordering = (
            "resource",
            "name",
        )
        unique_together = (("resource", "name"),)
