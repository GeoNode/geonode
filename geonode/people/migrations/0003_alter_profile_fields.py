# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0002_add_mapstory_specific_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='social_facebook',
            field=models.CharField(help_text='Provide your Facebook username', max_length=255, null=True, verbose_name='Facebook Profile', blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='social_github',
            field=models.CharField(help_text='Provide your GitHub username', max_length=255, null=True, verbose_name='GitHub Profile', blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='social_linkedin',
            field=models.CharField(help_text='Provide your LinkedIn username', max_length=255, null=True, verbose_name='LinkedIn Profile', blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='social_twitter',
            field=models.CharField(help_text='Provide your Twitter username', max_length=255, null=True, verbose_name='Twitter Handle', blank=True),
        ),
    ]
