# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0012_notifications_service'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationmetricdefinition',
            name='description',
            field=models.TextField(null=True),
        ),
    ]
