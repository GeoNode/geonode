# Populating polygons into bbox_polygon field

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0044_resourcebase_bbox_polygon'),
        ('layers', '0027_auto_20170801_1228_squashed_0033_auto_20180606_1543'),
    ]

    # This migration used to populate bbox_polygon field for all Layers.
    # Now all resources are updated in base/0044
    # See #12144

    operations = [
        migrations.RunPython(migrations.RunPython.noop, migrations.RunPython.noop),
    ]
