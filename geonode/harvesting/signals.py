from django.db.models.signals import pre_delete
from django.dispatch import receiver
from geonode.harvesting.models import Harvester
from geonode.base.models import ResourceBase


@receiver(pre_delete, sender=Harvester)
def delete_orphan_resources_on_harvester_delete(sender, instance, **kwargs):
    if instance.delete_orphan_resources_automatically:
        resource_ids = instance.harvestable_resources.filter(geonode_resource__isnull=False).values_list(
            "geonode_resource__id", flat=True
        )

        ResourceBase.objects.filter(id__in=resource_ids).delete()
