# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0029_layer_service'),
    ]

    operations = [
        migrations.CreateModel(
            name='GazetteerUpdateJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(default=b'pending', max_length=10, choices=[(b'pending', b'pending'), (b'failed', b'failed')])),
                ('layer', models.ForeignKey(to='layers.Layer', unique=True)),
            ],
        ),
    ]
