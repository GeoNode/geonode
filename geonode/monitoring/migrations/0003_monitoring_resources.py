# -*- coding: utf-8 -*-

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0002_monitoring_update'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='requestevent',
            name='resources',
        ),
        migrations.AddField(
            model_name='requestevent',
            name='resources',
            field=models.ManyToManyField(help_text='List of resources affected', to='monitoring.MonitoredResource', null=True, blank=True),
        ),
    ]
