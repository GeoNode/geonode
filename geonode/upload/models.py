import logging

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from geonode.layers.models import Dataset
from geonode.base.models import ResourceBase
from geonode.upload.orchestrator import orchestrator
from geonode.resource.models import ExecutionRequest


logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=Dataset)
def delete_dynamic_model(instance, sender, **kwargs):
    """
    Delete the dynamic relation and the geoserver layer
    """
    try:
        if instance.resourcehandlerinfo_set.exists():
            handler_module_path = instance.resourcehandlerinfo_set.first().handler_module_path
            handler = orchestrator.load_handler(handler_module_path)
            handler.delete_resource(instance)
        # Removing Field Schema
    except Exception as e:
        logger.error(f"Error during deletion instance deletion: {e}")


class ResourceHandlerInfo(models.Model):
    """
    Here we save the relation between the geonode resource created and the handler that created that resource
    """

    resource = models.ForeignKey(ResourceBase, blank=False, null=False, on_delete=models.CASCADE)
    handler_module_path = models.CharField(max_length=250, blank=False, null=False)
    execution_request = models.ForeignKey(ExecutionRequest, null=True, default=None, on_delete=models.SET_NULL)
    kwargs = models.JSONField(verbose_name="Storing strictly related information of the handler", default=dict)
