from django.contrib import admin

import geonode.contrib.groups.models


class GroupMemberInline(admin.TabularInline):
    model = geonode.contrib.groups.models.GroupMember


admin.site.register(geonode.contrib.groups.models.Group,
    inlines = [
        GroupMemberInline
    ]
)
admin.site.register(geonode.contrib.groups.models.GroupInvitation)
