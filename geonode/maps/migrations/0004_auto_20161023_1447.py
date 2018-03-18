# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maps', '0003_auto_20160827_1007'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='map',
            name='current_iteration',
        ),
        migrations.RemoveField(
            model_name='map',
            name='date_created',
        ),
        migrations.RemoveField(
            model_name='map',
            name='date_updated',
        ),
        migrations.RemoveField(
            model_name='map',
            name='group',
        ),
        migrations.RemoveField(
            model_name='map',
            name='last_auditor',
        ),
        migrations.RemoveField(
            model_name='map',
            name='status',
        ),
        migrations.AlterField(
            model_name='map',
            name='title_en',
            field=models.CharField(help_text='name by which the cited resource is known', max_length=255, null=True, verbose_name='* Title'),
        ),
        migrations.AlterField(
            model_name='wmsserver',
            name='ptype',
            field=models.CharField(default=b'gxp_wmscsource', max_length=50),
        ),
        migrations.AlterField(
            model_name='wmsserver',
            name='title',
            field=models.CharField(max_length=100, verbose_name='Your server name'),
        ),
        migrations.AlterField(
            model_name='wmsserver',
            name='url',
            field=models.URLField(help_text='http://example.com/geoserver/wms', max_length=500),
        ),
    ]
