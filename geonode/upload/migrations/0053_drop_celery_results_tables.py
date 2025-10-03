from django.db import migrations

def drop_django_celery_results_tables(apps, schema_editor):
    # Drop the tables if they exist (safe for fresh installs)
    schema_editor.execute("DROP TABLE IF EXISTS django_celery_results_taskresult;")
    schema_editor.execute("DROP TABLE IF EXISTS django_celery_results_chordcounter;")
    schema_editor.execute("DROP TABLE IF EXISTS django_celery_results_groupresult;")

class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0052_asset_upload_size'),
    ]

    operations = [
        migrations.RunPython(drop_django_celery_results_tables, reverse_code=migrations.RunPython.noop),
    ]