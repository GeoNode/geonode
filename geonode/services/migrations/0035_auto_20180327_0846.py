from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0034_auto_20180309_0917'),
    ]

    operations = [
        migrations.AlterField(
            model_name='service',
            name='type',
            field=models.CharField(max_length=10, choices=[('AUTO', 'Auto-detect'), ('OWS', 'Paired WMS/WFS/WCS'), ('WMS', 'Web Map Service'), ('CSW', 'Catalogue Service'), ('REST', 'ArcGIS REST Service'), ('OGP', 'OpenGeoPortal'), ('HGL', 'Harvard Geospatial Library'), ('GN_WMS', 'GeoNode (Web Map Service)'), ('GN_CSW', 'GeoNode (Catalogue Service)')]),
        ),
    ]
