# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0006_auto_20160908_0754'),
    ]

    operations = [
        migrations.CreateModel(
            name='Backup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(max_length=255, editable=False)),
                ('name', models.CharField(max_length=100)),
                ('name_en', models.CharField(max_length=100, null=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('description_en', models.TextField(null=True, blank=True)),
                ('location', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ('date',),
                'verbose_name_plural': 'Backups',
            },
        ),
        migrations.AlterField(
            model_name='contactrole',
            name='resource',
            field=models.ForeignKey(blank=True, to='base.ResourceBase', null=True),
        ),
        migrations.AlterField(
            model_name='link',
            name='resource',
            field=models.ForeignKey(blank=True, to='base.ResourceBase', null=True),
        ),
        migrations.AddField(
            model_name='backup',
            name='base_folder',
            field=models.CharField(default='/tmp/', max_length=100),
            preserve_default=False,
        ),
    ]
