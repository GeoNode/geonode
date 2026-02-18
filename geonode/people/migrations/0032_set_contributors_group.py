# Assign the contributors group to users according to #7364
from django.db import migrations
from django.db.migrations.operations import RunPython


def forwards_func(apps, schema_editor):
    from geonode.groups.conf import settings as groups_settings
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Profile = apps.get_model("people", "Profile")

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
        
    # Exclude anonymous user
    users_to_update = Profile.objects.exclude(username="AnonymousUser")
    for user in users_to_update:
        registeredmembers_group.user_set.add(user)
    # Exclude additional staff and superusers also
    for user in users_to_update.exclude(is_staff=True, is_superuser=True):
        cont_group.user_set.add(user)

def reverse_func(apps, schema_editor):
    # remove contributors group from users
    try:
        Group = apps.get_model("auth", "Group")
        Profile = apps.get_model("people", "Profile")
        cont_group = Group.objects.get(name='contributors')
        users_to_update = Profile.objects.filter(
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
