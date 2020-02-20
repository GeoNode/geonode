# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0030_auto_20171212_0518'),
        ('layers', '0028_auto_20171218_0249'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='service',
            field=models.ForeignKey(blank=True, on_delete=models.CASCADE, to='services.Service', null=True),
        ),
    ]
