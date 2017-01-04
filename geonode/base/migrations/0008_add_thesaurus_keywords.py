# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0007_auto_20160915_0944'),
    ]

    operations = [
        migrations.CreateModel(
            name='Thesaurus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(unique=True, max_length=255)),
                ('title', models.CharField(max_length=255)),
                ('date', models.CharField(default=b'', max_length=20)),
                ('description', models.TextField(default=b'', max_length=255)),
                ('slug', models.CharField(default=b'', max_length=64)),
            ],
            options={
                'ordering': ('identifier',),
                'verbose_name_plural': 'Thesauri',
            },
        ),
        migrations.CreateModel(
            name='ThesaurusKeyword',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('about', models.CharField(max_length=255, null=True, blank=True)),
                ('alt_label', models.CharField(default=b'', max_length=255, null=True, blank=True)),
                ('thesaurus', models.ForeignKey(related_name='thesaurus', to='base.Thesaurus')),
            ],
            options={
                'ordering': ('alt_label',),
                'verbose_name_plural': 'Thesaurus Keywords',
            },
        ),
        migrations.CreateModel(
            name='ThesaurusKeywordLabel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lang', models.CharField(max_length=3)),
                ('label', models.CharField(max_length=255)),
                ('keyword', models.ForeignKey(related_name='keyword', to='base.ThesaurusKeyword')),
            ],
            options={
                'ordering': ('keyword', 'lang'),
                'verbose_name_plural': 'Labels',
            },
        ),
        migrations.AlterUniqueTogether(
            name='thesauruskeywordlabel',
            unique_together=set([('keyword', 'lang')]),
        ),
        migrations.AlterUniqueTogether(
            name='thesauruskeyword',
            unique_together=set([('thesaurus', 'alt_label')]),
        ),
    ]
