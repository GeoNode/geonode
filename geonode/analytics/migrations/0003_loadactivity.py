# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('analytics', '0002_auto_20180131_0015'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoadActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('latitude', models.FloatField(help_text='Latitude', null=True, verbose_name='Latitude', blank=True)),
                ('longitude', models.FloatField(help_text='Longitude', null=True, verbose_name='Longitude', blank=True)),
                ('agent', models.CharField(help_text='User Agent', max_length=250, null=True, verbose_name='User Agent', blank=True)),
                ('ip', models.CharField(help_text='IP Address', max_length=100, null=True, verbose_name='IP Address', blank=True)),
                ('created_date', models.DateTimeField(help_text='Created Date', verbose_name='Created Date', auto_now_add=True)),
                ('last_modified', models.DateTimeField(help_text='Last Modified', verbose_name='Last Modified', auto_now=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
