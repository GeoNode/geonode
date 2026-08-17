from django.db import migrations

from geonode.base.enumerations import SOURCE_TYPE_REMOTE


def flag_harvested_resources_as_remote(apps, schema_editor):
    """Harvested resources are remote, but until #14524 sourcetype was only set when the remote
    provided no lat/lon bbox. Resources coming from a remote GeoNode were left as LOCAL, which also
    prevented remote_service/remote_typename from being assigned."""
    HarvestableResource = apps.get_model("harvesting", "HarvestableResource")
    ResourceBase = apps.get_model("base", "ResourceBase")
    Dataset = apps.get_model("layers", "Dataset")
    Service = apps.get_model("services", "Service")

    harvested = HarvestableResource.objects.filter(geonode_resource__isnull=False)
    ResourceBase.objects.filter(pk__in=harvested.values("geonode_resource_id")).exclude(
        sourcetype=SOURCE_TYPE_REMOTE
    ).update(sourcetype=SOURCE_TYPE_REMOTE)

    for service in Service.objects.filter(harvester__isnull=False):
        resource_ids = list(
            harvested.filter(harvester_id=service.harvester_id).values_list("geonode_resource_id", flat=True)
        )
        if not resource_ids:
            continue
        # remote_typename lives on the parent table, so it needs its own update
        ResourceBase.objects.filter(pk__in=resource_ids, remote_typename__isnull=True).update(
            remote_typename=service.name
        )
        Dataset.objects.filter(pk__in=resource_ids, remote_service__isnull=True).update(remote_service=service)


class Migration(migrations.Migration):
    dependencies = [
        ("harvesting", "0050_alter_harvester_harvester_type"),
        ("base", "0100_migrate_extrametadata_to_sparsefields"),
        ("layers", "0047_alter_dataset_store"),
        ("services", "0061_alter_service_base_url"),
    ]

    operations = [
        migrations.RunPython(flag_harvested_resources_as_remote, migrations.RunPython.noop),
    ]
