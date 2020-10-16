# Populating polygons into bbox_polygon field

from django.db import migrations
from django.contrib.gis.geos import Polygon


def populate_polygon(apps, schema_editor):
    Layer = apps.get_model('layers', 'Layer')
    for layer in Layer.objects.all():
        bbox = [getattr(layer, key, None) for key in ('bbox_x0', 'bbox_y0', 'bbox_x1', 'bbox_y1')]
        if all(bbox):
            layer.bbox_polygon = Polygon.from_bbox(bbox)
            layer.save()


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0044_resourcebase_bbox_polygon'),
        ('layers', '0027_auto_20170801_1228_squashed_0033_auto_20180606_1543'),
    ]

    operations = [
        migrations.RunPython(populate_polygon, lambda a, b: True),
    ]
