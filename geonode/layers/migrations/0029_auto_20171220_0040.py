# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('layers', '0028_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='StyleExtension',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('json_field', models.TextField(help_text='Designates json field.', verbose_name='Json Field', blank=True)),
                ('sld_body', models.TextField(help_text='Designates SLD Text.', verbose_name='SLD Text', blank=True)),
                ('created_date', models.DateTimeField(help_text='Designates when this record created.', verbose_name='Created Date', auto_now_add=True)),
                ('last_modified', models.DateTimeField(help_text='Designates when this record last modified.', verbose_name='Last Modified', auto_now=True)),
                ('created_by', models.ForeignKey(related_name='layer_style_created_by', verbose_name='Created by', to=settings.AUTH_USER_MODEL, help_text='Designates user who creates the record.')),
                ('layer', models.ForeignKey(verbose_name='Layer', to='layers.Layer', help_text='Designats related layer')),
                ('modified_by', models.ForeignKey(related_name='layer_style_modified_by', verbose_name='Modified by', to=settings.AUTH_USER_MODEL, help_text='Designates user who updates the record.')),
                ('style', models.OneToOneField(verbose_name='Style', to='layers.Style', help_text='Designats related Style')),
            ],
        ),
        migrations.RemoveField(
            model_name='layerstyle',
            name='layer',
        ),
        migrations.DeleteModel(
            name='LayerStyle',
        ),
    ]
