# -*- coding: utf-8 -*-
from django.contrib import admin
from geonode.people.models import Contact, Role
from geonode.layers.models import ContactRole

class ContactRoleInline(admin.TabularInline):
    model = ContactRole

class ContactAdmin(admin.ModelAdmin):
    inlines = [ContactRoleInline]

admin.site.register(Contact, ContactAdmin)
admin.site.register(Role)
