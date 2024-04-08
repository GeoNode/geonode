from django.db import migrations, connection

from geonode.storage.manager import storage_manager
from geonode.thumbs.thumbnails import _generate_thumbnail_name
import logging
logger = logging.getLogger(__name__)


def update_thumbnail_urls_and_delete_curated_thumbs_folder(apps, schema_editor):
    query = '''
    SELECT base_resourcebase.id, base_curatedthumbnail.img FROM base_resourcebase
    INNER JOIN base_curatedthumbnail
    ON base_resourcebase.id=base_curatedthumbnail.resource_id;
    '''
    # use historical model
    ResourceBase = apps.get_model('base', 'ResourceBase')

    c = connection.cursor()
    c.execute(query)
    results = c.fetchall()
    for result in results:
        resource_id, image = result
        resource = ResourceBase.objects.filter(id=resource_id).first()
        try:
            bytes_file = storage_manager.open(image).read()
        except Exception:
            bytes_file = None

        if resource and bytes_file:
            try:
                filename = _generate_thumbnail_name(resource.get_real_instance())
                resource.save_thumbnail(filename, bytes_file)
            except Exception as e:
                logger.error(f'Error during updating resource: {e.args[0]}', exc_info=e)


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0073_resourcebase_thumbnail_path'),
        ('layers', '0044_alter_dataset_unique_together'),
    ]

    operations = [
        migrations.RunPython(update_thumbnail_urls_and_delete_curated_thumbs_folder, migrations.RunPython.noop)
    ]
