# -*- coding: utf-8 -*-

from django.db import migrations, models
import jsonfield.fields
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ExceptionEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(db_index=True)),
                ('received', models.DateTimeField(db_index=True)),
                ('error_type', models.CharField(max_length=255, db_index=True)),
                ('error_data', models.TextField(default='')),
            ],
        ),
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('ip', models.GenericIPAddressField()),
                ('active', models.BooleanField(default=True)),
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
            name='MetricLabel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(default='', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='MetricValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('valid_from', models.DateTimeField(db_index=True)),
                ('valid_to', models.DateTimeField(db_index=True)),
                ('value', models.CharField(max_length=255)),
                ('value_num', models.DecimalField(default=None, null=True, max_digits=16, decimal_places=4, blank=True)),
                ('value_raw', models.TextField(default=None, null=True, blank=True)),
                ('data', jsonfield.fields.JSONField(default={})),
                ('label', models.ForeignKey(to='monitoring.MetricLabel', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='MonitoredResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default='', max_length=255, blank=True)),
                ('type', models.CharField(default='', max_length=255, choices=[('','No resource'), ('layer','Layer'), ('map','Map'), ('document','Document'), ('style','Style'), ('admin','Admin'), ('other','Other')])),
            ],
        ),
        migrations.CreateModel(
            name='RequestEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(db_index=True)),
                ('received', models.DateTimeField(db_index=True)),
                ('ows_type', models.CharField(default='other', max_length=255, choices=[('TMS','TMS'), ('WMS-C','WMS-C'), ('WMTS','WMTS'), ('WCS','WCS'), ('WFS','WFS'), ('WMS','WMS'), ('WPS','WPS'), ('other','Other')])),
                ('host', models.CharField(default='', max_length=255, blank=True)),
                ('request_path', models.CharField(default='', max_length=255)),
                ('resources', models.TextField(default='', help_text='Resources name (style, layer, document, map)', blank=True)),
                ('request_method', models.CharField(max_length=16, choices=[('GET','GET'), ('POST','POST'), ('HEAD','HEAD'), ('OPTIONS','OPTIONS'), ('PUT','PUT'), ('DELETE','DELETE')])),
                ('response_status', models.PositiveIntegerField()),
                ('response_size', models.PositiveIntegerField(default=0)),
                ('response_time', models.PositiveIntegerField(default=0, help_text='Response processing time in ms')),
                ('response_type', models.CharField(default='', max_length=255, null=True, blank=True)),
                ('user_agent', models.CharField(default=None, max_length=255, null=True, blank=True)),
                ('user_agent_family', models.CharField(default=None, max_length=255, null=True, blank=True)),
                ('client_ip', models.GenericIPAddressField()),
                ('client_lat', models.DecimalField(default=None, null=True, max_digits=8, decimal_places=5, blank=True)),
                ('client_lon', models.DecimalField(default=None, null=True, max_digits=8, decimal_places=5, blank=True)),
                ('client_country', models.CharField(default=None, max_length=255, null=True, blank=True)),
                ('client_region', models.CharField(default=None, max_length=255, null=True, blank=True)),
                ('client_city', models.CharField(default=None, max_length=255, null=True, blank=True)),
                ('custom_id', models.CharField(default=None, max_length=255, null=True, db_index=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('check_interval', models.DurationField(default=datetime.timedelta(0, 60))),
                ('last_check', models.DateTimeField(null=True, blank=True)),
                ('active', models.BooleanField(default=True)),
                ('notes', models.TextField(null=True, blank=True)),
                ('url', models.URLField(default='', null=True, blank=True)),
                ('host', models.ForeignKey(to='monitoring.Host', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='ServiceType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, choices=[('geonode','GeoNode'), ('geoserver','GeoServer'), ('hostgeoserver','Host (GeoServer)'), ('hostgeonode','Host (GeoNode)')])),
            ],
        ),
        migrations.CreateModel(
            name='ServiceTypeMetric',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('metric', models.ForeignKey(to='monitoring.Metric', on_delete=models.CASCADE)),
                ('service_type', models.ForeignKey(to='monitoring.ServiceType', on_delete=models.CASCADE)),
            ],
        ),
        migrations.AddField(
            model_name='service',
            name='service_type',
            field=models.ForeignKey(to='monitoring.ServiceType', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='requestevent',
            name='service',
            field=models.ForeignKey(to='monitoring.Service', on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='monitoredresource',
            unique_together=set([('name', 'type')]),
        ),
        migrations.AddField(
            model_name='metricvalue',
            name='resource',
            field=models.ForeignKey(to='monitoring.MonitoredResource', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='metricvalue',
            name='service',
            field=models.ForeignKey(to='monitoring.Service', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='metricvalue',
            name='service_metric',
            field=models.ForeignKey(to='monitoring.ServiceTypeMetric', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='exceptionevent',
            name='request',
            field=models.ForeignKey(to='monitoring.RequestEvent', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='exceptionevent',
            name='service',
            field=models.ForeignKey(to='monitoring.Service', on_delete=models.CASCADE),
        ),
    ]
