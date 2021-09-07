# Assign the contributors group to users according to #7364
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from django.db import migrations
from django.db.migrations.operations import RunPython


def forwards_func(apps, schema_editor):
    from geonode.groups.conf import settings as groups_settings

    # assign contributors group to users
    cont_group, _ = Group.objects.get_or_create(name='contributors')
    registeredmembers_group, _ = Group.objects.get_or_create(name=groups_settings.REGISTERED_MEMBERS_GROUP_NAME)
    ctype = ContentType.objects.get_for_model(cont_group)
    perm, _ = Permission.objects.get_or_create(
        codename='base_addresourcebase',
        name='Can add resources',
        content_type=ctype,
        )
    if perm:
        cont_group.permissions.add(perm)
    # Exclude admins and anonymous user
    users_to_update = get_user_model().objects.filter(pk__gt=0)
    for user in users_to_update:
        registeredmembers_group.user_set.add(user)
    for user in users_to_update.exclude(is_staff=True, is_superuser=True):
        cont_group.user_set.add(user)

def reverse_func(apps, schema_editor):
    # remove contributors group from users
    try:
        cont_group = Group.objects.get(name='contributors')
        users_to_update = get_user_model().objects.filter(
            pk__gt=0, is_staff=False, is_superuser=False
            )
        for user in users_to_update:
            user.groups.remove(cont_group)
    except Exception:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0031_merge_20210205_0824'),
    ]

    operations = [
        RunPython(forwards_func, reverse_func)
    ]
