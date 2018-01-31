# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0030_remove_styleextension_layer'),
    ]

    operations = [
        migrations.AddField(
            model_name='styleextension',
            name='title',
            field=models.CharField(default='54cba430-940d-4b78-83da-a6f2e83da759', help_text='Designats title of the SLD', max_length=50, verbose_name='Title'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='styleextension',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, help_text='Designats uuid', editable=False, verbose_name='UUID'),
        ),
    ]
