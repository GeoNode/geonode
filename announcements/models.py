from django.db import models
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

# support custom user models in django 1.5+
# https://docs.djangoproject.com/en/1.5/topics/auth/customizing/#substituting-a-custom-user-model
try:
    from django.contrib.auth import get_user_model
except ImportError:
    from django.contrib.auth.models import User
else:
    User = get_user_model()

class Announcement(models.Model):
    """
    A single announcement.
    """
    DISMISSAL_NO = 1
    DISMISSAL_SESSION = 2
    DISMISSAL_PERMANENT = 3
    
    DISMISSAL_CHOICES = [
        (DISMISSAL_NO, _("No Dismissals Allowed")),
        (DISMISSAL_SESSION, _("Session Only Dismissal")),
        (DISMISSAL_PERMANENT, _("Permanent Dismissal Allowed"))
    ]

    LEVEL_GENERAL = 1
    LEVEL_WARNING = 2
    LEVEL_CRITICAL = 3

    LEVEL_CHOICES = [
        (LEVEL_GENERAL, _("General")),
        (LEVEL_WARNING, _("Warning")),
        (LEVEL_CRITICAL, _("Critical"))
    ]
    
    title = models.CharField(_("title"), max_length=50)
    level = models.IntegerField(choices=LEVEL_CHOICES, default=LEVEL_GENERAL)
    content = models.TextField(_("content"))
    creator = models.ForeignKey(User, verbose_name=_("creator"))
    creation_date = models.DateTimeField(_("creation_date"), default=timezone.now)
    site_wide = models.BooleanField(_("site wide"), default=False)
    members_only = models.BooleanField(_("members only"), default=False)
    dismissal_type = models.IntegerField(choices=DISMISSAL_CHOICES, default=DISMISSAL_SESSION)
    publish_start = models.DateTimeField(_("publish_start"), default=timezone.now)
    publish_end = models.DateTimeField(_("publish_end"), blank=True, null=True)
    
    def get_absolute_url(self):
        return reverse("announcements_detail", args=[self.pk])
    
    def dismiss_url(self):
        if self.dismissal_type != Announcement.DISMISSAL_NO:
            return reverse("announcements_dismiss", args=[self.pk])

    @property
    def level_css(self):
        if self.level==self.LEVEL_WARNING:
            return "alert-warning"
        elif self.level==self.LEVEL_CRITICAL:
            return "alert-danger"
        else:
            return ""

    @property
    def level_label(self):
        return self.get_level_display()

    def __unicode__(self):
        return self.title
    
    class Meta:
        verbose_name = _("announcement")
        verbose_name_plural = _("announcements")


class Dismissal(models.Model):
    user = models.ForeignKey(User, related_name="announcement_dismissals")
    announcement = models.ForeignKey(Announcement, related_name="dismissals")
    dismissed_at = models.DateTimeField(default=timezone.now)
