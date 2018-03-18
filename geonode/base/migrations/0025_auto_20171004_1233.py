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
    ]
