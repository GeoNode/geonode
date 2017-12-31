# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0030_remove_styleextension_layer'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('maps', '0026_auto_20171004_1319'),
    ]

    operations = [
        migrations.CreateModel(
            name='MapLayerStyle',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, help_text='Designats uuid', editable=False, verbose_name='UUID')),
                ('name', models.CharField(help_text='Designats name of the SLD', max_length=50, verbose_name='Name')),
                ('json_field', models.TextField(help_text='Designates json field.', verbose_name='Json Field', blank=True)),
                ('sld_body', models.TextField(help_text='Designates SLD Text.', verbose_name='SLD Text', blank=True)),
                ('created_date', models.DateTimeField(help_text='Designates when this record created.', verbose_name='Created Date', auto_now_add=True)),
                ('last_modified', models.DateTimeField(help_text='Designates when this record last modified.', verbose_name='Last Modified', auto_now=True)),
                ('created_by', models.ForeignKey(related_name='map_layer_style_created_by', verbose_name='Created by', to=settings.AUTH_USER_MODEL, help_text='Designates user who creates the record.')),
                ('layer', models.ForeignKey(verbose_name='Layer', to='layers.Layer', help_text='Designats related layer')),
                ('map', models.ForeignKey(verbose_name='Map', to='maps.Map', help_text='Designats related Map')),
                ('modified_by', models.ForeignKey(related_name='map_layer_style_modified_by', verbose_name='Modified by', to=settings.AUTH_USER_MODEL, help_text='Designates user who updates the record.')),
            ],
        ),
    ]
