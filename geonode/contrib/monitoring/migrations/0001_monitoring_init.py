# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(db_index=True)),
                ('received', models.DateTimeField(db_index=True)),
                ('value', models.CharField(max_length=255)),
                ('value_num', models.DecimalField(default=None, null=True, max_digits=16, decimal_places=4, blank=True)),
                ('value_raw', models.TextField(default=None, null=True, blank=True)),
                ('data', jsonfield.fields.JSONField(default={})),
            ],
        ),
        migrations.CreateModel(
            name='ExceptionEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(db_index=True)),
                ('received', models.DateTimeField(db_index=True)),
                ('error_type', models.CharField(max_length=255, db_index=True)),
                ('error_data', models.TextField(default=b'')),
            ],
        ),
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('ip', models.GenericIPAddressField()),
            ],
        ),
        migrations.CreateModel(
            name='Metric',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='MetricType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=32, choices=[(b'counter', b'Counter'), (b'rate', b'Rate'), (b'value', b'Value')])),
                ('unit', models.CharField(default=b'', max_length=32, choices=[(b'', b'no unit'), (b'bps', b'bits per second'), (b'second', b'second'), (b'bit', b'bit'), (b'byte', b'byte'), (b'minute', b'minute')])),
            ],
        ),
        migrations.CreateModel(
            name='RequestEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(db_index=True)),
                ('received', models.DateTimeField(db_index=True)),
                ('ows_type', models.CharField(default=b'other', max_length=255, choices=[(b'TMS', b'TMS'), (b'WMS-C', b'WMS-C'), (b'WMTS', b'WMTS'), (b'WCS', b'WCS'), (b'WFS', b'WFS'), (b'WMS', b'WMS'), (b'WPS', b'WPS'), (b'other', b'Other')])),
                ('host', models.CharField(default=b'', max_length=255, blank=True)),
                ('request_path', models.CharField(default=b'', max_length=255)),
                ('resources', models.TextField(default=b'', help_text=b'Resources name (style, layer, document, map)', blank=True)),
                ('request_method', models.CharField(max_length=16, choices=[(b'GET', b'GET'), (b'POST', b'POST'), (b'HEAD', b'HEAD'), (b'OPTIONS', b'OPTIONS'), (b'PUT', b'PUT'), (b'DELETE', b'DELETE')])),
                ('response_status', models.PositiveIntegerField()),
                ('response_size', models.PositiveIntegerField(default=0)),
                ('response_time', models.PositiveIntegerField(default=0, help_text=b'Response processing time in ms')),
                ('response_type', models.CharField(default=b'', max_length=255)),
                ('user_agent', models.CharField(default=None, max_length=255, null=True, blank=True)),
                ('user_agent_family', models.CharField(default=None, max_length=255, null=True, blank=True)),
                ('client_ip', models.GenericIPAddressField()),
                ('client_lat', models.DecimalField(default=None, null=True, max_digits=8, decimal_places=5, blank=True)),
                ('client_lon', models.DecimalField(default=None, null=True, max_digits=8, decimal_places=5, blank=True)),
                ('client_country', models.CharField(default=None, max_length=255, null=True, blank=True)),
                ('client_region', models.CharField(default=None, max_length=255, null=True, blank=True)),
                ('client_city', models.CharField(default=None, max_length=255, null=True, blank=True)),
                ('custom_id', models.CharField(default=None, max_length=255, null=True, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('host', models.ForeignKey(to='monitoring.Host')),
            ],
        ),
        migrations.CreateModel(
            name='ServiceType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, choices=[(b'geonode', b'GeoNode'), (b'geoserver', b'GeoServer'), (b'host', b'Host')])),
            ],
        ),
        migrations.CreateModel(
            name='ServiceTypeMetric',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('metric', models.ForeignKey(to='monitoring.Metric')),
                ('service_type', models.ForeignKey(to='monitoring.ServiceType')),
            ],
        ),
        migrations.AddField(
            model_name='service',
            name='service_type',
            field=models.ForeignKey(to='monitoring.ServiceType'),
        ),
        migrations.AddField(
            model_name='requestevent',
            name='service',
            field=models.ForeignKey(to='monitoring.Service'),
        ),
        migrations.AddField(
            model_name='metric',
            name='type',
            field=models.ForeignKey(to='monitoring.MetricType'),
        ),
        migrations.AddField(
            model_name='exceptionevent',
            name='request',
            field=models.ForeignKey(to='monitoring.RequestEvent'),
        ),
        migrations.AddField(
            model_name='exceptionevent',
            name='service',
            field=models.ForeignKey(to='monitoring.Service'),
        ),
        migrations.AddField(
            model_name='event',
            name='service',
            field=models.ForeignKey(to='monitoring.Service'),
        ),
        migrations.AddField(
            model_name='event',
            name='service_type',
            field=models.ForeignKey(to='monitoring.ServiceTypeMetric'),
        ),
    ]
