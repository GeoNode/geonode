import logging

from django.db import migrations

from actstream.models import Action

logger = logging.getLogger(__name__)


def delete_comments_actions(apps, _):
    "Removes Action items related to comments"
    try:
        Action.objects.filter(
            action_object_content_type__model='comment').delete()
    except Exception as e:
        logger.exception(e)


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0083_clean_resources_with_missing_thumb'),
    ]

    operations = [
        migrations.RunPython(delete_comments_actions, migrations.RunPython.noop),
    ]
