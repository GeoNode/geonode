# -*- coding: utf-8 -*-

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0027_auto_20170801_1228'),
    ]

    operations = [
        migrations.AlterField(
            model_name='layer',
            name='default_style',
            field=models.ForeignKey(related_name='layer_default_style', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='layers.Style', null=True),
        ),
    ]
