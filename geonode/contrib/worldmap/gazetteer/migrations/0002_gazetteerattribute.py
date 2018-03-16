# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0029_layer_service'),
        ('gazetteer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GazetteerAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('in_gazetteer', models.BooleanField(default=False)),
                ('attribute', models.OneToOneField(to='layers.Attribute')),
            ],
        ),
    ]
