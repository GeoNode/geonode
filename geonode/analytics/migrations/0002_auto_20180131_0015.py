# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='layerload',
            name='created_date',
            field=models.DateTimeField(help_text='Created Date', verbose_name='Created Date', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='layerload',
            name='last_modified',
            field=models.DateTimeField(help_text='Last Modified', verbose_name='Last Modified', auto_now=True),
        ),
        migrations.AlterField(
            model_name='mapload',
            name='created_date',
            field=models.DateTimeField(help_text='Created Date', verbose_name='Created Date', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='mapload',
            name='last_modified',
            field=models.DateTimeField(help_text='Last Modified', verbose_name='Last Modified', auto_now=True),
        ),
        migrations.AlterField(
            model_name='pinpointuseractivity',
            name='created_date',
            field=models.DateTimeField(help_text='Created Date', verbose_name='Created Date', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='pinpointuseractivity',
            name='last_modified',
            field=models.DateTimeField(help_text='Last Modified', verbose_name='Last Modified', auto_now=True),
        ),
        migrations.AlterField(
            model_name='visitor',
            name='created_date',
            field=models.DateTimeField(help_text='Created Date', verbose_name='Created Date', auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='visitor',
            name='last_modified',
            field=models.DateTimeField(help_text='Last Modified', verbose_name='Last Modified', auto_now=True),
        ),
    ]
