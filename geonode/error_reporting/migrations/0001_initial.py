# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('django_db_logger', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ErrorLoggingAndReporting',
            fields=[
                ('statuslog_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='django_db_logger.StatusLog')),
                ('custom_msg', models.TextField()),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            bases=('django_db_logger.statuslog',),
        ),
    ]
