# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0003_monitoring_resources'),
    ]

    operations = [
        migrations.AddField(
            model_name='metric',
            name='type',
            field=models.CharField(default=b'rate', max_length=255, choices=[(b'rate', b'Rate'), (b'count', b'Count'), (b'value', b'Value')]),
        ),
        migrations.AlterField(
            model_name='exceptionevent',
            name='request',
            field=models.ForeignKey(related_name='exceptions', to='monitoring.RequestEvent'),
        ),
        migrations.AlterField(
            model_name='metricvalue',
            name='resource',
            field=models.ForeignKey(related_name='metric_values', to='monitoring.MonitoredResource'),
        ),
        migrations.AlterField(
            model_name='requestevent',
            name='resources',
            field=models.ManyToManyField(help_text=b'List of resources affected', related_name='requests', null=True, to='monitoring.MonitoredResource', blank=True),
        ),
        migrations.AlterField(
            model_name='servicetypemetric',
            name='metric',
            field=models.ForeignKey(related_name='service_type', to='monitoring.Metric'),
        ),
        migrations.AlterField(
            model_name='servicetypemetric',
            name='service_type',
            field=models.ForeignKey(related_name='metric', to='monitoring.ServiceType'),
        ),
    ]
