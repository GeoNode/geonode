# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risks', '0047_riskanalysisdymensioninfoassociation_resource'),
    ]

    operations = [
        migrations.AddField(
            model_name='riskanalysisdymensioninfoassociation',
            name='scenraio_description',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
