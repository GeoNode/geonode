# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0019_notification_check_def_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='metric',
            name='description',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
