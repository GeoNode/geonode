import sys
import traceback
from pprint import pprint
from slugify import slugify
from celery.task import task


from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import Group

from geonode.groups.models import GroupProfile, GroupMember

@task(name="geonode.tasks.requests.users", queue="users")

def join_user_to_groups(user, group_list):
    for g in group_list:
        pprint(g)
        group_profile, created = GroupProfile.objects.get_or_create(title=str(g), slug=slugify(g))
        try:
            group_member = GroupMember.objects.get(group=group_profile, user=user)
        except ObjectDoesNotExist as e:
            group_profile.join(user, role='member')
