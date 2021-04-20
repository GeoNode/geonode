from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Assign existing users to contributors group"
    )

    def handle(self, *args, **options):
        cont_group, created = Group.objects.get_or_create(name='contributors')
        ctype = ContentType.objects.get_for_model(cont_group)
        perm, created = Permission.objects.get_or_create(
            codename='base_addresourcebase',
            name='Can add resources',
            content_type=ctype,
            )
        if perm:
            cont_group.permissions.add(perm)
        # Exclude admins and anonymous user
        users_to_update = get_user_model().objects.filter(
            pk__gt=0, is_staff=False, is_superuser=False
            )
        for user in users_to_update:
            cont_group.user_set.add(user)
        self.stdout.write("All users are assigned to contributors group")
