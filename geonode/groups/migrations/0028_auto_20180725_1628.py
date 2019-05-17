# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0027_auto_20180105_1631'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupcategory',
            name='description',
            field=models.TextField(default=None, null=True, verbose_name='Description', blank=True),
        ),
        migrations.AlterField(
            model_name='groupcategory',
            name='name',
            field=models.CharField(unique=True, max_length=255, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='groupcategory',
            name='name_en',
            field=models.CharField(max_length=255, unique=True, null=True, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='groupprofile',
            name='categories',
            field=models.ManyToManyField(related_name='groups', verbose_name='Categories', to='groups.GroupCategory', blank=True),
        ),
    ]
