# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '24_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('base', '24_to_26'),
    ]

    operations = [
        migrations.CreateModel(
            name='DockedResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('group', models.ForeignKey(blank=True, to='groups.GroupProfile', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='FavoriteResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('group', models.ForeignKey(blank=True, to='groups.GroupProfile', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='KeywordIgnoreListModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=100, null=True, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='current_iteration',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='date_created',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 4, 12, 33, 14, 481108), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='date_updated',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 4, 12, 33, 21, 304750), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='group',
            field=models.ForeignKey(blank=True, to='groups.GroupProfile', null=True),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='last_auditor',
            field=models.ForeignKey(related_name='a_last_auditor', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='resource_type',
            field=models.CharField(default=b'', help_text='type of resource layer, map or document', max_length=50),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='status',
            field=models.CharField(default=b'DRAFT', max_length=10, choices=[(b'DRAFT', 'Draft'), (b'PENDING', 'Pending'), (b'ACTIVE', 'Active'), (b'INACTIVE', 'Inactive'), (b'DENIED', 'Denied'), (b'DELETED', 'Deleted'), (b'CANCELED', 'Canceled')]),
        ),
        migrations.AlterField(
            model_name='resourcebase',
            name='abstract',
            field=models.TextField(default=b'Abstract is very important! You are requested to update it now.', help_text='brief narrative summary of the content of the resource(s)', verbose_name='abstract', blank=True),
        ),
        migrations.AlterField(
            model_name='resourcebase',
            name='title',
            field=models.CharField(help_text='name by which the cited resource is known', max_length=255, verbose_name='* Title'),
        ),
        migrations.AlterField(
            model_name='topiccategory',
            name='description',
            field=models.TextField(default=b'', verbose_name='Field description'),
        ),
        migrations.AlterField(
            model_name='topiccategory',
            name='description_en',
            field=models.TextField(default=b'', null=True, verbose_name='Field description'),
        ),
        migrations.AlterField(
            model_name='topiccategory',
            name='is_choice',
            field=models.BooleanField(default=True, verbose_name='Is active'),
        ),
        migrations.AddField(
            model_name='favoriteresource',
            name='resource',
            field=models.ForeignKey(blank=True, to='base.ResourceBase', null=True),
        ),
        migrations.AddField(
            model_name='favoriteresource',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='dockedresource',
            name='resource',
            field=models.ForeignKey(blank=True, to='base.ResourceBase', null=True),
        ),
        migrations.AddField(
            model_name='dockedresource',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
