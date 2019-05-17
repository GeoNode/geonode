# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risks', '0034_auto_20170330_0631'),
    ]

    operations = [
        migrations.AlterField(
            model_name='analysistypefurtherresourceassociation',
            name='resource',
            field=models.ForeignKey(to='risks.FurtherResource'),
        ),
        migrations.AlterField(
            model_name='dymensioninfofurtherresourceassociation',
            name='resource',
            field=models.ForeignKey(to='risks.FurtherResource'),
        ),
    ]
