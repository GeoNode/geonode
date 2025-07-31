from django.db import migrations
from django.conf import settings


def create_asset_upload_size_limit(apps, schema_editor):
    UploadSizeLimit = apps.get_model("upload", "UploadSizeLimit")
    obj = {
        "slug": "asset_upload_size",
        "description": "Max size for the uploaded assets file via API",
        "max_size": settings.DEFAULT_MAX_UPLOAD_SIZE
    }
    UploadSizeLimit.objects.create(**obj)


def remove_asset_upload_size_limit(apps, schema_editor):
    UploadSizeLimit = apps.get_model("upload", "UploadSizeLimit")
    UploadSizeLimit.objects.filter(slug="asset_upload_size").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0051__align_resourcehandler_with_asset'),
    ]

    operations = [
        migrations.RunPython(create_asset_upload_size_limit, remove_asset_upload_size_limit),
    ]
