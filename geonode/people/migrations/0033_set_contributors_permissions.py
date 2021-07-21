# Assign the contributors group to users according to #7364

from django.db import migrations
from django.db.utils import IntegrityError
from django.db.migrations.operations import RunPython
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from geonode.base.models import ResourceBase


def assign_permissions_to_contributors(apps, schema_editor):
    contributors = Group.objects.filter(name='contributors')
    if contributors.exists():
        contr_obj = contributors.get()
        try:
            perm, _ = Permission.objects.update_or_create(
                codename='add_resourcebase',
                defaults=dict(
                    name='Can add resources',
                    content_type=ContentType.objects.get_for_model(ResourceBase)
                )
            )
            contr_obj.permissions.add(perm)
            contr_obj.save()
            contr_obj.permissions.filter(codename='base_addresourcebase').delete()
        except IntegrityError:
            pass
    Permission.objects.filter(codename='base_addresourcebase').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0032_set_contributors_group'),
    ]

    operations = [
        RunPython(assign_permissions_to_contributors, migrations.RunPython.noop)
    ]
