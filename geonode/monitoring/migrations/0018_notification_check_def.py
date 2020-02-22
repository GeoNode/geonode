# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0017_monitoring_notification_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationmetricdefinition',
            name='max_value',
            field=models.DecimalField(default=None, null=True, max_digits=16, decimal_places=4, blank=True),
        ),
        migrations.AddField(
            model_name='notificationmetricdefinition',
            name='min_value',
            field=models.DecimalField(default=None, null=True, max_digits=16, decimal_places=4, blank=True),
        ),
        migrations.AddField(
            model_name='notificationmetricdefinition',
            name='steps',
            field=models.PositiveIntegerField(default=None, null=True, blank=True),
        ),
    ]
