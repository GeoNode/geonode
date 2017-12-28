from django.contrib import admin
from .models import Message, Thread, UserThread

import autocomplete_light


class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'thread')
    list_display_links = ('id',)


class ThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject')
    list_display_links = ('id',)


class UserThreadAdmin(admin.ModelAdmin):
    list_display = ('id',)
    list_display_links = ('id',)


admin.site.register(Message, MessageAdmin)
admin.site.register(Thread, ThreadAdmin)
admin.site.register(UserThread, UserThreadAdmin)
