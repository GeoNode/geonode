# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_auto_20160824_0245'),
    ]

    operations = [
        migrations.CreateModel(
            name='HierarchicalKeyword',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100, verbose_name='Name')),
                ('slug', models.SlugField(unique=True, max_length=100, verbose_name='Slug')),
                ('path', models.CharField(unique=True, max_length=255)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TaggedContentItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='resourcebase',
            name='keywords',
            field=taggit.managers.TaggableManager(to='base.HierarchicalKeyword', through='base.TaggedContentItem',
                                                  blank=True, help_text="""commonly used word(s) or formalised word(s)
                                                   or phrase(s) used to describe the subject
                                                    (space or comma-separated)""",
                                                  verbose_name='keywords'),
        ),
        migrations.AddField(
            model_name='taggedcontentitem',
            name='content_object',
            field=models.ForeignKey(to='base.ResourceBase'),
        ),
        migrations.AddField(
            model_name='taggedcontentitem',
            name='tag',
            field=models.ForeignKey(related_name='keywords', to='base.HierarchicalKeyword'),
        ),
    ]
