# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0030_auto_20171212_0518'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='proxy_base',
            field=models.URLField(null=True, blank=True),
        ),
    ]
