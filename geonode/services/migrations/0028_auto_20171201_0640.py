# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0027_harvestjob_details'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='servicelayer',
            name='description',
        ),
        migrations.RemoveField(
            model_name='servicelayer',
            name='styles',
        ),
        migrations.RemoveField(
            model_name='servicelayer',
            name='title',
        ),
        migrations.RemoveField(
            model_name='servicelayer',
            name='typename',
        ),
    ]
