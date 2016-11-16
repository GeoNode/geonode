from django.contrib import admin

from announcements.models import Announcement, Dismissal

# import our user model and determine the field we will use to search by user
# support custom user models & username fields in django 1.5+
try:
    from django.contrib.auth import get_user_model
except ImportError:
    from django.contrib.auth.models import User
    username_search = "user__username"
else:
    User = get_user_model()
    if hasattr(User, "USERNAME_FIELD"):
        username_search = "user__%s" % User.USERNAME_FIELD
    else:
        username_search = "user__username"

class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "level", "creator", "creation_date", "members_only")
    list_filter = ("members_only",)
    fieldsets = [
        (None, {
            "fields": ["title", "level", "content", "site_wide", "members_only", "publish_start", "publish_end", "dismissal_type"],
        }),
    ]

    def save_model(self, request, obj, form, change):
        if not change:
            # When creating a new announcement, set the creator field.
            obj.creator = request.user
        obj.save()

class DismissalAdmin(admin.ModelAdmin):
    list_display = ("user", "announcement", "dismissed_at")
    search_fields = (username_search, "announcement__title")

admin.site.register(Announcement, AnnouncementAdmin)
admin.site.register(Dismissal, DismissalAdmin)
