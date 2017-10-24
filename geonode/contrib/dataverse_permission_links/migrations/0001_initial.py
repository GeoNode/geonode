# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DataversePermissionLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'auto-filled on save', max_length=255, blank=True)),
                ('dataverse_username', models.CharField(max_length=255, verbose_name=b'Dataverse username')),
                ('worldmap_username', models.CharField(help_text=b'(Validated on save)', max_length=255, verbose_name=b'Worldmap username')),
                ('is_active', models.BooleanField(default=True)),
                ('description', models.TextField(help_text=b'optional', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('worldmap_user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, help_text=b'auto-filled on save', null=True)),
            ],
            options={
                'db_table': 'dataverse_permission_links',
            },
        ),
        migrations.AlterUniqueTogether(
            name='dataversepermissionlink',
            unique_together=set([('dataverse_username', 'worldmap_user')]),
        ),
    ]
