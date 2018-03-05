# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcebase',
            name='docked',
            field=models.BooleanField(default=False, help_text='Should this resource be docked in home page?', verbose_name='Docked'),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='favorite',
            field=models.BooleanField(default=False, help_text='Should this resource be in favorite list ?', verbose_name='Favorite'),
        ),
    ]
