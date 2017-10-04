# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0025_auto_20171004_1258'),
        ('layers', '0025_auto_20171004_1231'),
    ]

    operations = [
        migrations.CreateModel(
            name='LayerAuditActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('result', models.CharField(max_length=15, choices=[(b'APPROVED', 'Approved'), (b'DECLEINED', 'Decleined'), (b'CANCELED', 'Canceled')])),
                ('comment_subject', models.CharField(help_text='Comment type to approve or deny layer submission ', max_length=300)),
                ('comment_body', models.TextField(help_text='Comments when auditor denied or approved layer submission', null=True, blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('auditor', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='LayerSubmissionActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('iteration', models.IntegerField(default=0)),
                ('is_audited', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('group', models.ForeignKey(to='groups.GroupProfile')),
                ('layer', models.ForeignKey(related_name='layer_submission', to='layers.Layer')),
            ],
        ),
        migrations.AddField(
            model_name='layerauditactivity',
            name='layer_submission_activity',
            field=models.ForeignKey(to='layers.LayerSubmissionActivity'),
        ),
        migrations.AlterUniqueTogether(
            name='layersubmissionactivity',
            unique_together=set([('layer', 'group', 'iteration')]),
        ),
    ]
