from geonode.people.models import Contact, ContactRole, Role
from django.contrib import admin

class ContactAdmin(admin.ModelAdmin):
    inlines = [ContactRoleInline]

class ContactRoleInline(admin.TabularInline):
    model = ContactRole

class ContactRoleAdmin(admin.ModelAdmin):
    model = ContactRole
    list_display_links = ('id',)
    list_display = ('id','contact', 'layer', 'role')
    list_editable = ('contact', 'layer', 'role')

admin.site.register(Contact, ContactAdmin)
admin.site.register(ContactRole, ContactRoleAdmin)
admin.site.register(Role)
