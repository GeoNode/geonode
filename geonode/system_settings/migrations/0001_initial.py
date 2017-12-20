# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('settings_code', models.CharField(help_text='Settings For', unique=True, max_length=250, verbose_name='Settings For', choices=[(b'location', 'LOCATION'), (b'elevation', 'ELEVATION')])),
                ('value', models.CharField(help_text='Value', max_length=255, null=True, verbose_name='Value', blank=True)),
                ('object_id', models.PositiveIntegerField()),
                ('created_date', models.DateTimeField(help_text='Created Date', verbose_name='Created Date', auto_now_add=True)),
                ('last_modified', models.DateTimeField(help_text='Last Modified', verbose_name='Last Modified', auto_now=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('created_by', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('modified_by', models.ForeignKey(related_name='layer_style_modified_by', verbose_name='Modified by', to=settings.AUTH_USER_MODEL, help_text='Designates user who updates the record.')),
            ],
        ),
    ]
