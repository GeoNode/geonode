from django.contrib import admin

from geonode.groups.models import GroupMember, GroupProfile, GroupInvitation


class GroupMemberInline(admin.TabularInline):
    model = GroupMember


class GroupAdmin(admin.ModelAdmin):
    inlines = [
        GroupMemberInline
    ]
    exclude = ['group', ]

admin.site.register(GroupProfile, GroupAdmin)

admin.site.register(GroupInvitation)
