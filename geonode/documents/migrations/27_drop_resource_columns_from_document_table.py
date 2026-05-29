from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '26_move_data_to_documentresourcelink_table'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='document',
            name='object_id',
        ),
    ]
