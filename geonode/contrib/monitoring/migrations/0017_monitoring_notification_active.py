# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0016_notification_severity'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationcheck',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
