import json
import logging

from django.db import migrations

logger = logging.getLogger(__name__)


def migrate_extrametadata_to_sparsefields(apps, schema_editor):
    """
    Migrate ExtraMetadata entries to SparseField entries.

    Each ExtraMetadata object (with its JSON dict) is stored as a single
    SparseField entry with name 'extra_metadata_<pk>' and value as JSON string.
    Entries whose serialized JSON exceeds 1024 characters are skipped with a warning.
    """
    ExtraMetadata = apps.get_model("base", "ExtraMetadata")
    SparseField = apps.get_model("metadata", "SparseField")

    for extra_meta in ExtraMetadata.objects.select_related("resource").iterator():
        name = f"extra_metadata_{extra_meta.pk}"
        value = json.dumps(extra_meta.metadata)
        if len(value) > 1024:
            logger.warning(
                f"ExtraMetadata pk={extra_meta.pk} skipped during migration to SparseField: "
                f"serialized value exceeds 1024 characters"
            )
            continue
        SparseField.objects.get_or_create(
            resource=extra_meta.resource,
            name=name,
            defaults={"value": value},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0097_alter_link_asset"),
        ("metadata", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(migrate_extrametadata_to_sparsefields, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="resourcebase",
            name="metadata",
        ),
        migrations.DeleteModel(
            name="ExtraMetadata",
        ),
    ]
