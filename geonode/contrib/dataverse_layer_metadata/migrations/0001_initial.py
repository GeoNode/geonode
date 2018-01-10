# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0028_auto_20170919_1550'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataverseLayerMetadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dv_user_id', models.IntegerField(db_index=True)),
                ('dv_username', models.CharField(max_length=255)),
                ('dv_user_email', models.EmailField(max_length=254)),
                ('return_to_dataverse_url', models.URLField(max_length=255, blank=True)),
                ('datafile_download_url', models.URLField(max_length=255)),
                ('dataverse_installation_name', models.CharField(default=b'Harvard Dataverse', help_text=b'url to Harvard Dataverse, Odum Institute Dataverse, etc', max_length=255)),
                ('dataverse_id', models.IntegerField(default=-1, help_text=b'id in database')),
                ('dataverse_name', models.CharField(max_length=255, db_index=True)),
                ('dataverse_description', models.TextField(blank=True)),
                ('dataset_id', models.IntegerField(default=-1, help_text=b'id in database')),
                ('dataset_version_id', models.IntegerField(default=-1, help_text=b'id in database')),
                ('dataset_semantic_version', models.CharField(help_text=b'example: "DRAFT",  "1.2", "2.3", etc', max_length=25, blank=True)),
                ('dataset_name', models.CharField(max_length=255, blank=True)),
                ('dataset_citation', models.TextField()),
                ('dataset_description', models.TextField(blank=True)),
                ('dataset_is_public', models.BooleanField(default=False)),
                ('datafile_id', models.IntegerField(default=-1, help_text=b'id in database', db_index=True)),
                ('datafile_label', models.CharField(help_text=b'original file name', max_length=255)),
                ('datafile_expected_md5_checksum', models.CharField(max_length=100)),
                ('datafile_filesize', models.IntegerField(help_text=b'in bytes')),
                ('datafile_content_type', models.CharField(max_length=255)),
                ('datafile_create_datetime', models.DateTimeField()),
                ('datafile_is_restricted', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('map_layer', models.ForeignKey(to='layers.Layer')),
            ],
            options={
                'ordering': ('-modified',),
                'verbose_name_plural': 'Dataverse Metadata',
            },
        ),
    ]
