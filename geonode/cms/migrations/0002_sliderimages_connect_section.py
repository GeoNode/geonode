# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sliderimages',
            name='connect_section',
            field=models.ForeignKey(related_name='linksection', verbose_name='Connect section', blank=True, to='cms.SectionManagementTable', null=True),
        ),
    ]
