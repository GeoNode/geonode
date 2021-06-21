from django.db import migrations


def forwards(apps, schema_editor):
    Document = apps.get_model('documents', 'Document')
    DocumentResourceLink = apps.get_model('documents', 'DocumentResourceLink')

    DocumentResourceLink.objects.bulk_create(
        DocumentResourceLink(
            document_id=document.id,
            content_type_id=document.content_type_id,
            object_id=document.object_id,
        )
        for document in Document.objects.exclude(
            content_type_id__isnull=True,
            object_id__isnull=True,
        )
    )


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '25_add_documentresourcelink_table'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
