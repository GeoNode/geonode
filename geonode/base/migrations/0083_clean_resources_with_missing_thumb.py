import logging

from django.db import migrations
from django.templatetags.static import static

from geonode.thumbs.utils import MISSING_THUMB

logger = logging.getLogger(__name__)


def set_null_thumbnail(apps, _):
    "Sets thumbnail_url to null for resources with thumbnail_url=missing_thumb"
    try:
        resource_model = apps.get_model('base', 'ResourceBase')
        link_model = apps.get_model('base', 'Link')
        # update thumbnail urls
        resource_model.objects.filter(thumbnail_url__icontains=static(MISSING_THUMB)).update(thumbnail_url=None)
        # Remove thumbnail links
        link_model.objects.filter(resource__thumbnail_url__isnull=True, name='Thumbnail').delete()
    except Exception as e:
        logger.exception(e)


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0082_remove_dialogos_comment'),
    ]

    operations = [
        migrations.RunPython(set_null_thumbnail, migrations.RunPython.noop),
    ]
