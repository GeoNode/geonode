# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0028_auto_20171201_0640'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='servicelayer',
            name='layer',
        ),
        migrations.RemoveField(
            model_name='servicelayer',
            name='service',
        ),
        migrations.DeleteModel(
            name='ServiceLayer',
        ),
    ]
