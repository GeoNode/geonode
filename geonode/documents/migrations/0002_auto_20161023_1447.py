# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='current_iteration',
        ),
        migrations.RemoveField(
            model_name='document',
            name='date_created',
        ),
        migrations.RemoveField(
            model_name='document',
            name='date_updated',
        ),
        migrations.RemoveField(
            model_name='document',
            name='group',
        ),
        migrations.RemoveField(
            model_name='document',
            name='last_auditor',
        ),
        migrations.RemoveField(
            model_name='document',
            name='status',
        ),
        migrations.AlterField(
            model_name='document',
            name='title_en',
            field=models.CharField(help_text='name by which the cited resource is known', max_length=255, null=True, verbose_name='* Title'),
        ),
    ]
