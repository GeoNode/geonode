# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0009_sample_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='metric',
            name='unit',
            field=models.CharField(blank=True, max_length=255, null=True, choices=[(b'B', b'Bytes'), (b'MB', b'Megabytes'), (b'GB', b'Gigabytes'), (b'B/s', b'Bytes per second'), (b'MB/s', b'Megabytes per second'), (b'GB/s', b'Gigabytes per second'), (b's', b'Seconds'), (b'Rate', b'Rate'), (b'%', b'Percentage'), (b'Count', b'Count')]),
        ),
        migrations.AlterField(
            model_name='metricvalue',
            name='ows_service',
            field=models.ForeignKey(related_name='metric_values', blank=True, to='monitoring.OWSService', null=True),
        ),
        migrations.AlterField(
            model_name='owsservice',
            name='name',
            field=models.CharField(unique=True, max_length=16, choices=[(b'TMS', b'TMS'), (b'WMS-C', b'WMS-C'), (b'WMTS', b'WMTS'), (b'WCS', b'WCS'), (b'WFS', b'WFS'), (b'WMS', b'WMS'), (b'WPS', b'WPS'), (b'all', b'All'), (b'other', b'Other')]),
        ),
    ]
