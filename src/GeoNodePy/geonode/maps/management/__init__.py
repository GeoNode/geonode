from django.conf import settings
from django.utils.translation import ugettext_noop as _
from django.db.models.signals import post_syncdb 

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification

    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type("upload_successful", _("External Upload Successful"), _("the external upload you provided succeeded"), default=1)
        notification.create_notice_type("upload_failed", _("External Upload Failed"), _("the external upload you provided failed"), default=1)
                               
    post_syncdb.connect(create_notice_types, sender=notification)
else:
    print "Skipping creation of NoticeTypes as notification app not found"

