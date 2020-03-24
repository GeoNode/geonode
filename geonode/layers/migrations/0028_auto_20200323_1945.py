# Populating polygons into bbox_polygon field

from django.db import migrations
from django.contrib.gis.geos import Polygon


def populate_polygon(apps, schema_editor):
    Layer = apps.get_model('layers', 'Layer')
    for layer in Layer.objects.all():
        bbox_tup = (layer.bbox_x0, layer.bbox_y0, layer.bbox_x1, layer.bbox_y1)
        layer.bbox_polygon = Polygon.from_bbox(bbox_tup)
        layer.save()


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0042_resourcebase_bbox_polygon'),
        ('layers', '0027_auto_20170801_1228_squashed_0033_auto_20180606_1543'),
    ]

    operations = [
        migrations.RunPython(populate_polygon, lambda a, b: True),
    ]
