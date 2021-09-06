from django.db import migrations
from django.db.migrations.operations import RunPython
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model



def create_group_and_assign_perms_forward_func(apps, schema_editor):
    # create moderators group and assign permissions to it.
    moderators_group, _ = Group.objects.get_or_create(name='moderators')
    ctype = ContentType.objects.get_for_model(moderators_group)
    approve_perm, _ = Permission.objects.get_or_create(
        codename='approve_resources',
        name='Can approve resources',
        content_type=ctype,
        )
    publish_perm, _ = Permission.objects.get_or_create(
        codename='publish_resources',
        name='Can publish resources',
        content_type=ctype,
        )
    moderators_group.permissions.add(approve_perm, publish_perm)


def remove_group_and_unassign_perms_reverse_func(apps, schema_editor):
    # remove users from moderators group
    try:
        moderators_group = Group.objects.get(name='moderators')
        users_to_update = get_user_model().objects.filter(groups__in=[moderators_group])
        for user in users_to_update:
            user.groups.remove(moderators_group)
        moderators_group.delete()
    except Exception:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0036_merge_20210706_0951'),
    ]

    operations = [
        RunPython(
            create_group_and_assign_perms_forward_func,
            remove_group_and_unassign_perms_reverse_func
        )
    ]
