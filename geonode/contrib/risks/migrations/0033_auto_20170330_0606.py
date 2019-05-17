# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risks', '0032_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dymensioninfofurtherresourceassociation',
            name='dymension_info',
        ),
        migrations.AddField(
            model_name='dymensioninfofurtherresourceassociation',
            name='dimension_info',
            field=models.ForeignKey(related_name='further_resource', default='', to='risks.DymensionInfo'),
            preserve_default=False,
        ),
    ]
