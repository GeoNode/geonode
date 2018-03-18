# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('layers', '0026_auto_20171004_1311'),
        ('documents', '0026_auto_20171004_1243'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentLayers',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'db_table': 'document_layers',
            },
        ),
        migrations.RemoveField(
            model_name='document',
            name='content_type',
        ),
        migrations.AddField(
            model_name='documentlayers',
            name='document',
            field=models.ForeignKey(to='documents.Document'),
        ),
        migrations.AddField(
            model_name='documentlayers',
            name='layer',
            field=models.ForeignKey(blank=True, to='layers.Layer', null=True),
        ),
        migrations.AddField(
            model_name='document',
            name='layers',
            field=models.ManyToManyField(to='layers.Layer', null=True, through='documents.DocumentLayers', blank=True),
        ),
    ]
