# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0002_news_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='news',
            name='image',
            field=models.ImageField(null=True, upload_to=b'news_updates', blank=True),
        ),
    ]
