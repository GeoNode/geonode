# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0002_questionanswer'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupprofile',
            name='docked',
            field=models.BooleanField(default=False, help_text='Should this organization be docked in home page?', verbose_name='Docked'),
        ),
        migrations.AddField(
            model_name='groupprofile',
            name='favorite',
            field=models.BooleanField(default=False, help_text='Should this organization be in favorite list ?', verbose_name='Favorite'),
        ),
    ]
