# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_alter_resourcebase_fields'),
        ('maps', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MapStory',
            fields=[
                ('resourcebase_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='base.ResourceBase')),
            ],
            options={
                'abstract': False,
                'db_table': 'maps_mapstory',
                'verbose_name_plural': 'MapStories',
            },
            bases=('base.resourcebase',),
        ),
        migrations.AlterModelOptions(
            name='map',
            options={'verbose_name_plural': 'MapStory Chapters'},
        ),
        migrations.AddField(
            model_name='map',
            name='chapter_index',
            field=models.IntegerField(null=True, verbose_name='chapter index', blank=True),
        ),
        migrations.AddField(
            model_name='map',
            name='story',
            field=models.ForeignKey(related_name='chapter_list', blank=True, to='maps.MapStory', null=True),
        ),
    ]
