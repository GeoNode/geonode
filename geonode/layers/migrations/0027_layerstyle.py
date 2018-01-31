# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0026_auto_20171004_1311'),
    ]

    operations = [
        migrations.CreateModel(
            name='LayerStyle',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='Designates layer styles name.', max_length=25, verbose_name='Style Name')),
                ('layer', models.ForeignKey(verbose_name='Layer', to='layers.Layer', help_text='Designats related layer')),
            ],
        ),
    ]
