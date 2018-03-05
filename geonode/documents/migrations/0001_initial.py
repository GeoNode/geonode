# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('base', '__first__'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('resourcebase_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='base.ResourceBase')),
                ('title_en', models.CharField(help_text='name by which the cited resource is known', max_length=255, null=True, verbose_name='title')),
                ('abstract_en', models.TextField(help_text='brief narrative summary of the content of the resource(s)', null=True, verbose_name='abstract', blank=True)),
                ('purpose_en', models.TextField(help_text='summary of the intentions with which the resource(s) was developed', null=True, verbose_name='purpose', blank=True)),
                ('constraints_other_en', models.TextField(help_text='other restrictions and legal prerequisites for accessing and using the resource or metadata', null=True, verbose_name='restrictions other', blank=True)),
                ('supplemental_information_en', models.TextField(default='No information provided', help_text='any other descriptive information about the dataset', null=True, verbose_name='supplemental information')),
                ('data_quality_statement_en', models.TextField(help_text="general explanation of the data producer's knowledge about the lineage of a dataset", null=True, verbose_name='data quality statement', blank=True)),
                ('doc_file', models.FileField(max_length=255, upload_to=b'documents', null=True, verbose_name='File', blank=True)),
                ('extension', models.CharField(max_length=128, null=True, blank=True)),
                ('doc_type', models.CharField(max_length=128, null=True, blank=True)),
                ('doc_url', models.URLField(help_text='The URL of the document if it is external.', max_length=255, null=True, verbose_name='URL', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('base.resourcebase',),
        ),
        migrations.CreateModel(
            name='DocumentAuditActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('result', models.CharField(max_length=15, choices=[(b'APPROVED', 'Approved'), (b'DECLINED', 'Declined'), (b'CANCELED', 'Canceled')])),
                ('comment_subject', models.CharField(help_text='Comment type to approve or deny layer submission ', max_length=300)),
                ('comment_body', models.TextField(help_text='Comments when auditor denied or approved layer submission', blank=True)),
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
