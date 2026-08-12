from django.db import migrations
from geonode.upload.orchestrator import orchestrator
from geonode.documents.models import Document


def document_migration(apps, _):
    NewResources = apps.get_model("upload", "ResourceHandlerInfo")
    handler_to_use = orchestrator.load_handler_by_id("document")
    if not handler_to_use:
        return

    for old_resource in Document.objects.exclude(
        pk__in=NewResources.objects.values_list("resource_id", flat=True)
    ):
        try:
            handler_to_use().create_resourcehandlerinfo(
                handler_module_path=str(handler_to_use()),
                resource=old_resource,
                execution_id=None,
                kwargs={"is_legacy": True},
            )
        except Exception as e:
            print(e)
            continue


class Migration(migrations.Migration):
    dependencies = [
        ("upload", "0053_drop_celery_results_tables"),
    ]

    operations = [
        migrations.RunPython(document_migration),
    ]
