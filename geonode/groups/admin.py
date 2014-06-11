from django.contrib import admin

from geonode.groups.models import GroupMember, Group, GroupInvitation


class GroupMemberInline(admin.TabularInline):
    model = GroupMember


class GroupAdmin(admin.ModelAdmin):
    inlines = [
        GroupMemberInline
    ]

admin.site.register(Group, GroupAdmin)

admin.site.register(GroupInvitation)
