# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '24_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('documents', '0025_auto_20171004_1233'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentAuditActivity',
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
            name='DocumentSubmissionActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('iteration', models.IntegerField(default=0)),
                ('is_audited', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('document', models.ForeignKey(related_name='document_submission', to='documents.Document')),
                ('group', models.ForeignKey(to='groups.GroupProfile')),
            ],
        ),
        migrations.AddField(
            model_name='documentauditactivity',
            name='document_submission_activity',
            field=models.ForeignKey(to='documents.DocumentSubmissionActivity'),
        ),
        migrations.AlterUniqueTogether(
            name='documentsubmissionactivity',
            unique_together=set([('document', 'group', 'iteration')]),
        ),
    ]
