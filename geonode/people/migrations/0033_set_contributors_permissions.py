# Assign the contributors group to users according to #7364

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import migrations
from django.db.migrations.operations import RunPython
from geonode.base.models import ResourceBase


def assign_permissions_to_contributors(apps, schema_editor):
    contributors = Group.objects.filter(name='contributors')
    if contributors.exists():
        contr_obj = contributors.first()
        perm, _ = Permission.objects.update_or_create(
            codename='add_resourcebase',
            defaults=dict(
                name='Can add resources',
                content_type=ContentType.objects.get_for_model(ResourceBase)
            )
        )
        contr_obj.permissions.add(perm)
        perm_exists = contr_obj.permissions.filter(codename='base_addresourcebase')
        if perm_exists.exists():
            contr_obj.permissions.remove(perm_exists.first())
        contr_obj.save()
    perm_to_remove = Permission.objects.filter(codename='base_addresourcebase')
    if perm_to_remove.exists():
        perm_to_remove.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0032_set_contributors_group'),
    ]

    operations = [
        RunPython(assign_permissions_to_contributors)
    ]
