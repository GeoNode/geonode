# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0004_monitoring_metric_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='OWSService',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=16, choices=[('TMS','TMS'), ('WMS-C','WMS-C'), ('WMTS','WMTS'), ('WCS','WCS'), ('WFS','WFS'), ('WMS','WMS'), ('WPS','WPS'), ('other','Other')])),
            ],
        ),
        migrations.RemoveField(
            model_name='requestevent',
            name='ows_type',
        ),
        migrations.AlterField(
            model_name='metricvalue',
            name='label',
            field=models.ForeignKey(related_name='metric_values',
                                    to='monitoring.MetricLabel', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='metricvalue',
            name='ows_service',
            field=models.ForeignKey(blank=True, to='monitoring.OWSService', on_delete=models.CASCADE, null=True),
        ),
        migrations.AddField(
            model_name='requestevent',
            name='ows_service',
            field=models.ForeignKey(blank=True, to='monitoring.OWSService', on_delete=models.CASCADE, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='metricvalue',
            unique_together=set([('valid_from', 'valid_to', 'service', 'service_metric', 'resource', 'label', 'ows_service')]),
        ),
    ]
