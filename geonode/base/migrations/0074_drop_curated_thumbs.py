import os
import shutil

from django.db import migrations, connection
from django.conf import settings

from geonode.base.models import ResourceBase
from geonode.storage.manager import storage_manager
from geonode.thumbs.thumbnails import _generate_thumbnail_name


def update_thumbnail_urls_and_delete_curated_thumbs_folder(apps, schema_editor):
    query = '''
    SELECT base_resourcebase.id, base_curatedthumbnail.img FROM base_resourcebase
    INNER JOIN base_curatedthumbnail
    ON base_resourcebase.id=base_curatedthumbnail.resource_id;
    '''
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
            filename = _generate_thumbnail_name(resource.get_real_instance())
            resource.save_thumbnail(filename, bytes_file)

    # delete curated_thumbs folder
    curated_thumbs_folder= os.path.abspath(f"{settings.MEDIA_ROOT}/curated_thumbs")
    try:
        shutil.rmtree(curated_thumbs_folder)
    except OSError as e:
        print(f"Error deleting curated_thumbs folder: {e}.")

class Migration(migrations.Migration):

    dependencies = [
        ('base', '0073_resourcebase_thumbnail_path'),
    ]

    operations = [
        migrations.RunPython(update_thumbnail_urls_and_delete_curated_thumbs_folder)
    ]