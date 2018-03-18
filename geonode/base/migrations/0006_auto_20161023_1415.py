# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0005_auto_20161023_1415'),
        ('base', '0005_remove_resourcebase_a_date_created'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcebase',
            name='a_current_iteration',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='a_date_created',
            field=models.DateTimeField(default=datetime.datetime(2016, 10, 23, 14, 15, 21, 665811), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='a_date_updated',
            field=models.DateTimeField(default=datetime.datetime(2016, 10, 23, 14, 15, 31, 558697), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='a_group',
            field=models.ForeignKey(blank=True, to='groups.GroupProfile', null=True),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='a_last_auditor',
            field=models.ForeignKey(related_name='a_last_auditor', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='resourcebase',
            name='a_status',
            field=models.CharField(default=b'DRAFT', max_length=10, choices=[(b'DRAFT', 'Draft'), (b'PENDING', 'Pending'), (b'ACTIVE', 'Active'), (b'INACTIVE', 'Inactive'), (b'DENIED', 'Denied'), (b'DELETED', 'Deleted'), (b'CANCELED', 'Canceled')]),
        ),
    ]
