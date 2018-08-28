# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0029_auto_20171203_1624'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='webserviceharvestlayersjob',
            name='service',
        ),
        migrations.DeleteModel(
            name='WebServiceRegistrationJob',
        ),
        migrations.AlterField(
            model_name='harvestjob',
            name='status',
            field=models.CharField(default=b'QUEUED', max_length=15, choices=[(b'QUEUED', b'QUEUED'), (b'CANCELLED', b'QUEUED'), (b'IN_PROCESS', b'IN_PROCESS'), (b'PROCESSED', b'PROCESSED'), (b'FAILED', b'FAILED')]),
        ),
        migrations.DeleteModel(
            name='WebServiceHarvestLayersJob',
        ),
    ]
