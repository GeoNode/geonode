from django.contrib import admin

import geonode.contrib.groups.models


class GroupMemberInline(admin.TabularInline):
    model = geonode.contrib.groups.models.GroupMember


class GroupAdmin(admin.ModelAdmin):
    inlines = [
        GroupMemberInline
    ]
    exclude = ('django_group',)

admin.site.register(geonode.contrib.groups.models.Group, GroupAdmin)

admin.site.register(geonode.contrib.groups.models.GroupInvitation)
