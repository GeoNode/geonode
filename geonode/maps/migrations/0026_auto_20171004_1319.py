# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0025_auto_20171004_1258'),
        ('maps', '0025_auto_20171004_1233'),
    ]

    operations = [
        migrations.CreateModel(
            name='MapAuditActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('result', models.CharField(max_length=15, choices=[(b'APPROVED', 'Approved'), (b'DECLINED', 'Declined'), (b'CANCELED', 'Canceled')])),
                ('comment_subject', models.CharField(help_text='Comment type to approve or deny layer submission ', max_length=300)),
                ('comment_body', models.TextField(help_text='Comments when auditor denied or approved layer submission', null=True, blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('auditor', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MapSubmissionActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('iteration', models.IntegerField(default=0)),
                ('is_audited', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('group', models.ForeignKey(to='groups.GroupProfile')),
                ('map', models.ForeignKey(related_name='map_submission', to='maps.Map')),
            ],
        ),
        migrations.CreateModel(
            name='WmsServer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ptype', models.CharField(default=b'gxp_wmscsource', max_length=50)),
                ('url', models.URLField(help_text='http://example.com/geoserver/wms', max_length=500)),
                ('title', models.CharField(max_length=100, verbose_name='Your server name')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='mapauditactivity',
            name='map_submission_activity',
            field=models.ForeignKey(to='maps.MapSubmissionActivity'),
        ),
        migrations.AlterUniqueTogether(
            name='mapsubmissionactivity',
            unique_together=set([('map', 'group', 'iteration')]),
        ),
    ]
