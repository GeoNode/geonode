from django.db import migrations


def update_resource_type(apps, schema_editor):
    """Updating Layer 'resource_type' from 'layer' to 'dataset'
    """
    MyModel = apps.get_model('layers', 'Dataset')
    _models = MyModel.objects.filter(resource_type='layer')
    for _m in _models:
        _m.resource_type='dataset'
    
    MyModel.objects.bulk_update(_models, ['resource_type'])



class Migration(migrations.Migration):

    dependencies = [
        ('layers', '0040_dataset_ows_url'),
    ]

    operations = [
        migrations.RunPython(update_resource_type, migrations.RunPython.noop),
    ]
