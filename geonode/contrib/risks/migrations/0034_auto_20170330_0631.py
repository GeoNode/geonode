# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risks', '0033_auto_20170330_0606'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dymensioninfofurtherresourceassociation',
            name='dimension_info',
            field=models.ForeignKey(to='risks.DymensionInfo'),
        ),
    ]
