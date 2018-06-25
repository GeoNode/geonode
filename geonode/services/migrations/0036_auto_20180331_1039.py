# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0035_auto_20180327_0846'),
    ]

    operations = [
        migrations.AlterField(
            model_name='service',
            name='type',
            field=models.CharField(max_length=10, choices=[(b'AUTO', 'Auto-detect'), (b'OWS', 'Paired WMS/WFS/WCS'), (b'WMS', 'Web Map Service'), (b'CSW', 'Catalogue Service'), (b'REST_MAP', 'ArcGIS REST MapServer'), (b'REST_IMG', 'ArcGIS REST ImageServer'), (b'OGP', 'OpenGeoPortal'), (b'HGL', 'Harvard Geospatial Library'), (b'GN_WMS', 'GeoNode (Web Map Service)'), (b'GN_CSW', 'GeoNode (Catalogue Service)')]),
        ),
    ]
