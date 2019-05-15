# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risks', '26_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='riskanalysis',
            name='data_file',
            field=models.FileField(max_length=255, upload_to=b'metadata_files'),
        ),
        migrations.AlterField(
            model_name='riskanalysis',
            name='descriptor_file',
            field=models.FileField(max_length=255, upload_to=b'descriptor_files'),
        ),
        migrations.AlterField(
            model_name='riskanalysis',
            name='metadata_file',
            field=models.FileField(max_length=255, upload_to=b'metadata_files'),
        ),
        migrations.AlterField(
            model_name='riskanalysiscreate',
            name='descriptor_file',
            field=models.FileField(max_length=255, upload_to=b'descriptor_files'),
        ),
        migrations.AlterField(
            model_name='riskanalysisimportdata',
            name='data_file',
            field=models.FileField(max_length=255, upload_to=b'data_files'),
        ),
        migrations.AlterField(
            model_name='riskanalysisimportmetadata',
            name='metadata_file',
            field=models.FileField(max_length=255, upload_to=b'metadata_files'),
        ),
    ]
