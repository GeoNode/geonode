# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '24_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HarvestJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resource_id', models.CharField(max_length=255)),
                ('status', models.CharField(default=b'QUEUED', max_length=15, choices=[(b'QUEUED', b'QUEUED'), (b'IN_PROCESS', b'IN_PROCESS'), (b'PROCESSED', b'PROCESSED'), (b'FAILED', b'FAILED')])),
                ('service', models.OneToOneField(to='services.Service')),
            ],
        ),
    ]
