from django.db import migrations


def update_upload_size_limit_objects(apps, schema_editor):
    UploadSizeLimit = apps.get_model("upload", "UploadSizeLimit")
    
    UploadSizeLimit.objects.filter(slug="total_upload_size_sum").update(slug="dataset_upload_size")

    UploadSizeLimit.objects.filter(slug="file_upload_handler").update(
        description='Request total size, validated before the upload process. This should be greater than "dataset_upload_size".')


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0033_auto_20210531_1252'),
    ]

    operations = [
        migrations.RunPython(update_upload_size_limit_objects, migrations.RunPython.noop),
    ]
