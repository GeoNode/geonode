# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('documents', '24_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentResourceLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
        ),
        migrations.AddField(
            model_name='documentresourcelink',
            name='document',
            field=models.ForeignKey(related_name='links', to='documents.Document'),
        ),
    ]
