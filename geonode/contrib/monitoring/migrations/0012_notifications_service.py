# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0011_notification_def'),
    ]

    operations = [
        migrations.AlterField(
            model_name='metric',
            name='type',
            field=models.CharField(default=b'rate', max_length=255, choices=[(b'rate', b'Rate'), (b'count', b'Count'), (b'value', b'Value'), (b'value_numeric', b'Value numeric')]),
        ),
        migrations.AlterField(
            model_name='metricnotificationcheck',
            name='service',
            field=models.ForeignKey(related_name='checks', blank=True, to='monitoring.Service', null=True),
        ),
    ]
