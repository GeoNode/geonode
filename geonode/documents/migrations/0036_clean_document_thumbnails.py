import logging

from django.db import migrations

from ..models import Document

logger = logging.getLogger(__name__)


def set_null_to_non_image_docs_thumbnails(apps, _):
    "Sets thumbnail_url to null for documents which are not images"
    try:
        # update thumbnail urls
        for document in Document.objects.all():
            if not document.is_image:
                document.thumbnail_url=None
                document.save()
        # Remove thumbnail links
        link_model = apps.get_model('base', 'Link')
        link_model.objects.filter(resource__thumbnail_url__isnull=True, name='Thumbnail').delete()
    except Exception as e:
        logger.exception(e)


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0033_remove_document_doc_type'),
    ]

    operations = [
        migrations.RunPython(set_null_to_non_image_docs_thumbnails, migrations.RunPython.noop),
    ]
