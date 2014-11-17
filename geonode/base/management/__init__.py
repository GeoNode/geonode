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
                "request_download_resourcebase",
                _("Request to download a resource"),
                _("A request for downloading a resource was sent"))

        signals.post_syncdb.connect(
            create_notice_types,
            sender=notification.models)
        logger.info(
            "Notifications Configured for geonode.base.management.commands")
else:
    logger.info(
        "Skipping creation of NoticeTypes for geonode.base.management.commands, since notification app was not found.")
