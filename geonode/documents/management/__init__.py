from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _
import logging
logger = logging.getLogger(__name__)

if "notification" in settings.INSTALLED_APPS:
    import notification

    if hasattr(notification, 'models'):
        def create_notice_types(app, created_models, verbosity, **kwargs):
            notification.models.NoticeType.create(
                "document_created",
                _("Document Created"),
                _("A Document was created"))
            notification.models.NoticeType.create(
                "document_updated",
                _("Document Updated"),
                _("A Document was updated"))
            notification.models.NoticeType.create(
                "document_deleted",
                _("Document Deleted"),
                _("A Document was deleted"))
            notification.models.NoticeType.create(
                "document_comment",
                _("Comment on Document"),
                _("A Document was commented on"))
            notification.models.NoticeType.create(
                "document_rated",
                _("Document for Map"),
                _("A rating was given to a document"))

        signals.post_syncdb.connect(
            create_notice_types,
            sender=notification.models)
        logger.info(
            "Notifications Configured for geonode.documents.management.commands")
else:
    logger.info(
        "Skipping creation of NoticeTypes for geonode.documents.management.commands,"
        " since notification app was not found.")
