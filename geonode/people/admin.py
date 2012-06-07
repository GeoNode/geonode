from django.contrib import admin
from geonode.people.models import Contact, ContactRole, Role

class ContactRoleInline(admin.TabularInline):
    model = ContactRole

class ContactAdmin(admin.ModelAdmin):
    inlines = [ContactRoleInline]

class ContactRoleAdmin(admin.ModelAdmin):
    model = ContactRole
    list_display_links = ('id',)
    list_display = ('id','contact', 'layer', 'role')
    list_editable = ('contact', 'layer', 'role')

admin.site.register(Contact, ContactAdmin)
admin.site.register(ContactRole, ContactRoleAdmin)
admin.site.register(Role)
