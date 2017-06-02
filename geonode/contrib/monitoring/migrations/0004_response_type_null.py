# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0003_service_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requestevent',
            name='response_type',
            field=models.CharField(default=b'', max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='service',
            name='url',
            field=models.URLField(default=b'', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='servicetype',
            name='name',
            field=models.CharField(unique=True, max_length=255, choices=[(b'geonode', b'GeoNode'), (b'geoserver', b'GeoServer'), (b'hostgeoserver', b'Host (GeoServer)'), (b'hostgeonode', b'Host (GeoNode)')]),
        ),
    ]
