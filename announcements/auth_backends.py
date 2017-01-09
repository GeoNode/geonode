class AnnouncementPermissionsBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = True
    
    def authenticate(self, **kwargs):
        # always return a None user
        return None
    
    def has_perm(self, user, perm, obj=None):
        if perm == "announcements.can_manage":
            return user.is_authenticated() and user.is_staff
